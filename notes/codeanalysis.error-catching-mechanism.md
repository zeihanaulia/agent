# 🔍 Error Catching Mechanism in sandbox_executor.py

## Overview
Ada **3 layer error catching** di `sandbox_executor.py`:

---

## Layer 1: Critical Error Detection (`_is_critical_error` method)

### Location: Line 693-705

```python
def _is_critical_error(self, error_line: str) -> bool:
    """Check if error line indicates critical startup failure"""
    critical_patterns = [
        r'APPLICATION FAILED TO START',
        r'Port.*already in use',
        r'FATAL ERROR',
        r'OutOfMemoryError',
        r'ClassNotFoundException',
        r'No main class found'
    ]
    
    return any(re.search(pattern, error_line, re.IGNORECASE) for pattern in critical_patterns)
```

**Cara Kerja:**
- Memeriksa setiap log line apakah mengandung **critical error pattern**
- Pattern yang dicek: `APPLICATION FAILED TO START`, `Port already in use`, `FATAL ERROR`, dll
- Return `True` jika ditemukan critical error
- Return `False` jika tidak ada critical error

**Contoh Error yang Di-Catch:**
```
2025-11-13T06:37:01.784Z ERROR 621 --- [main] o.s.b.d.LoggingFailureAnalysisReporter:
***************************
APPLICATION FAILED TO START
***************************
```

---

## Layer 2: Execute Run dengan Monitoring

### Location: Line 532-628 (`execute_run` method)

Ini adalah **main catching mechanism** untuk run phase:

```python
# Step 1: Start application in background
start_result = self.sandbox.commands.run(
    'cd /app && (java -jar target/*.jar > spring.log 2>&1 &); sleep 2',
    timeout=10
)

# Step 2: Monitor logs dalam loop
for i in range(0, max_wait_time, check_interval):
    time.sleep(check_interval)
    
    # Baca logs
    log_result = self.sandbox.commands.run(
        'cd /app && tail -n 20 spring.log 2>/dev/null || echo "No logs yet"',
        timeout=5
    )
    
    if log_result.stdout:
        startup_logs.append(log_result.stdout)
        on_stdout(log_result.stdout)
        
        # ⚠️ CEK CRITICAL ERROR DI SINI
        if self._is_critical_error(log_result.stdout):
            critical_error = True
            print("❌ Critical startup error detected!")
            break  # ❌ STOP ITERASI, JANGAN LANJUT
```

**Flow:**
1. ✅ Start aplikasi di background
2. 🔄 Loop monitoring selama max 60 detik
3. 📋 Baca logs setiap 2 detik
4. 🔍 Periksa apakah ada critical error
5. ❌ Kalau ada critical error → **BREAK LOOP SEKALIGUS**
6. ✅ Kalau startup success → **BREAK LOOP JUGA**

**Output BuildResult:**
```python
# Jika critical error ditemukan
return BuildResult(
    success=False,
    output=all_logs,
    error_output=''.join(error_output),
    error_details="Critical startup error detected in application logs"
)
```

---

## Layer 3: Test Project dengan Retry Logic

### Location: Line 727-930 (`test_project` method)

Ini adalah **orchestration layer** yang menggunakan hasil dari execute_build dan execute_run:

```python
# Loop dengan retry logic
for iteration in range(1, self.config.max_retries + 1):
    print(f"\n🔄 Iteration {iteration}/{self.config.max_retries}")
    
    # Build phase
    build_result = self.execute_build()
    
    if build_result.success:
        # Run phase
        run_result = self.execute_run()
        
        if run_result.success:
            results['success'] = True
            results['final_status'] = 'success'
            return results  # ✅ SUCCESS, EXIT
        else:
            # ⚠️ Run failed, check if critical
            is_critical = run_result.error_details and any(
                pattern in run_result.error_details.upper() 
                for pattern in ['APPLICATION FAILED TO START', 'FATAL ERROR', 'OUTOFMEMORYERROR']
            )
            
            if is_critical:
                print("🚨 Critical startup error detected - stopping iterations")
                results['final_status'] = 'critical_error'
                results['error_analysis'].append({
                    'iteration': iteration,
                    'phase': 'run',
                    'error_type': run_result.error_type,
                    'error_details': run_result.error_details,
                    'suggested_fixes': run_result.suggested_fixes or []
                })
                return results  # ❌ EXIT, JANGAN RETRY
```

**Logic:**
```
if run_result.success:
    ✅ SUCCESS → EXIT DAN RETURN
else:
    ❌ FAILED
    if is_critical_error:
        ❌ CRITICAL → STOP RETRY & EXIT
    else:
        ⚠️ NOT CRITICAL → TRY NEXT ITERATION (auto-fix)
```

---

## 📊 Complete Error Catching Flow

```
┌─────────────────────────────────────────┐
│   execute_run() START                   │
│   Start Java application in background  │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│   Monitor Loop (60 seconds max)         │
│   Check logs every 2 seconds            │
└─────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
    CHECK: Is        CHECK: Is
    Startup         Critical
    Ready?          Error?
    (YES)           (YES)
        │               │
        │               ▼
        │   ┌──────────────────────┐
        │   │ _is_critical_error() │
        │   │                      │
        │   │ Pattern Match:       │
        │   │ - APPLICATION FAILED │
        │   │ - FATAL ERROR        │
        │   │ - OutOfMemoryError   │
        │   │ - etc                │
        │   └──────────────────────┘
        │               │
        │   ┌───────────┴──────────┐
        │   │                      │
        │   ▼                      ▼
        │ TRUE (Critical)    FALSE (Not Critical)
        │   │                      │
        │   ▼                      ▼
        │ BREAK LOOP          CONTINUE LOOP
        │   │                      │
        └───┴──────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────┐
        │  Return BuildResult      │
        │  success = RESULT        │
        └──────────────────────────┘
                  │
                  ▼
        ┌──────────────────────────┐
        │  test_project()          │
        │  Check run_result        │
        └──────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
    success=TRUE      success=FALSE
        │                   │
        ▼                   ▼
    EXIT OK         CHECK: Is Critical?
        │                   │
        │          ┌────────┴────────┐
        │          │                 │
        │          ▼                 ▼
        │      YES (Critical)    NO (Not)
        │          │                 │
        │          ▼                 ▼
        │      STOP RETRY        TRY AUTO-FIX
        │      EXIT              TRY NEXT ITER
        │          │                 │
        └──────────┴─────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │  Return Results          │
        │  final_status = ????     │
        └──────────────────────────┘
```

---

## ✅ Kesuksesan Dari User Error

Error yang di-catch dari terminal user:

```
APPLICATION FAILED TO START

Description:
The bean 'courierRepository', defined in com.example.springboot.delivery.ports.repository.CourierRepository...
could not be registered. A bean with that name has already been defined in 
com.example.springboot.delivery.port.persistence.CourierRepository...
```

### Pattern Match Check:
```python
# Line: "APPLICATION FAILED TO START"
critical_patterns = [
    r'APPLICATION FAILED TO START',  ✅ MATCH!
    ...
]

_is_critical_error(error_line) → True
```

### Result Flow:
1. ✅ `_is_critical_error()` mendeteksi `"APPLICATION FAILED TO START"`
2. ✅ Set `critical_error = True`
3. ✅ Break monitoring loop
4. ✅ Return BuildResult dengan `success=False`
5. ✅ test_project() menerima run_result dengan error
6. ✅ Check: `is_critical = True` (karena contain "APPLICATION FAILED TO START")
7. ✅ Set `final_status = 'critical_error'`
8. ✅ **EXIT tanpa retry** - jangan lanjut iterasi!

---

## 🎯 Key Points

| Aspek | Detail |
|-------|--------|
| **Error Detection** | Menggunakan regex pattern matching pada log output |
| **When** | Setiap kali baca logs (every 2 seconds) |
| **What** | Cek apakah ada string critical error patterns |
| **Action** | Break monitoring loop & return error status |
| **Layer** | Multiple layers: execute_run → test_project → flow_test_sandbox |
| **Stop Retry** | ✅ Ada - jangan lanjut iterate kalau critical error |
| **Auto-Fix** | ❌ Tidak di-apply untuk critical error (hanya BUILD error) |

---

## 📝 Summary

**Catching di sandbox_executor.py:**

1. **Detect**: `_is_critical_error()` method dengan regex patterns
2. **Monitor**: Loop setiap 2 detik dalam `execute_run()`
3. **Break**: Sebelum error jadi lebih parah, stop loop immediately
4. **Report**: Return BuildResult dengan error details
5. **Orchestrate**: test_project() melihat critical error & stop retry
6. **Output**: Error status & analysis di-pass ke workflow handler

**Result**: User error di-catch dengan benar ✅
