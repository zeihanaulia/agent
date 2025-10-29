package com.example.springboot;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    public String hello() {
        return "Hello from dataset-loaded Spring Boot app!";
    }

    @GetMapping("/")
    public String index() {
        return "Greetings from Spring Boot Zei!";
    }

}