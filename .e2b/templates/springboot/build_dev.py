from e2b import Template, default_build_logger
from template import template
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    Template.build(
        template,
        alias="springboot-dev",
        on_build_logs=default_build_logger(),
    )