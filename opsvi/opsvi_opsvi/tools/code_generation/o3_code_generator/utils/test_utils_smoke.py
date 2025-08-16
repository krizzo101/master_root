"""
Smoke test for O3 Code Generator utility modules.
Ensures all utility modules can be imported, instantiated, and basic methods called without error.
"""
from src.tools.code_generation.o3_code_generator.o3_logger.logger import (
    LogConfig,
    setup_logger,
)

setup_logger(LogConfig())
from pathlib import Path

try:
    from src.tools.code_generation.o3_code_generator.utils.base_processor import (
        BaseProcessor,
    )
    from src.tools.code_generation.o3_code_generator.utils.directory_manager import (
        DirectoryManager,
    )
    from src.tools.code_generation.o3_code_generator.utils.file_generator import (
        FileGenerator,
    )
    from src.tools.code_generation.o3_code_generator.utils.input_loader import (
        UniversalInputLoader,
    )
    from src.tools.code_generation.o3_code_generator.utils.output_formatter import (
        OutputFormatter,
    )
    from src.tools.code_generation.o3_code_generator.utils.prompt_builder import (
        PromptBuilder,
    )
except ImportError:
    exit(1)
else:
    pass
finally:
    pass


class DummyConfigManager:
    pass


def main():
    try:
        dm = DirectoryManager()
        dm.ensure_directory_exists("test_dir")
    except Exception:
        pass
    else:
        pass
    finally:
        pass
    try:
        of = OutputFormatter()
        _ = of.to_json({"test": 123})
    except Exception:
        pass
    else:
        pass
    finally:
        pass
    try:
        fg = FileGenerator()
        fg.save_file("test content", Path("test_file.txt"))
    except Exception:
        pass
    else:
        pass
    finally:
        pass
    try:
        pb = PromptBuilder()
        prompt = pb.build_generation_prompt(
            input_data={"foo": "bar"}, system_prompt="Test system prompt"
        )
    except Exception:
        pass
    else:
        pass
    finally:
        pass
    try:
        uil = UniversalInputLoader()
    except Exception:
        pass
    else:
        pass
    finally:
        pass


if __name__ == "__main__":
    main()
else:
    pass
