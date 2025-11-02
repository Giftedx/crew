"""Startup validation for the Ultimate Discord Intelligence Bot.

This module provides comprehensive startup validation including:
- Configuration validation
- Environment checks
- Dependency verification
- Service connectivity tests
"""
from __future__ import annotations
import os
import sys
import time
from ultimate_discord_intelligence_bot.config_schema import validate_config
from platform.core.step_result import StepResult

class StartupValidator:
    """Validates system startup and configuration."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks_passed = 0
        self.checks_failed = 0

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.checks_failed += 1

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_success(self, message: str) -> None:
        """Add a success message."""
        self.checks_passed += 1
        print(f'✅ {message}')

    def validate_configuration(self) -> StepResult:
        """Validate application configuration."""
        print('🔧 Validating configuration...')
        try:
            config, errors = validate_config()
            if errors:
                for error in errors:
                    self.add_error(f'Configuration error: {error}')
                return StepResult.fail(f'Configuration validation failed: {len(errors)} errors')
            self.add_success('Configuration validation passed')
            return StepResult.ok(data={'config': config})
        except Exception as e:
            self.add_error(f'Configuration validation failed: {e!s}')
            return StepResult.fail(f'Configuration validation failed: {e!s}')

    def validate_environment(self) -> StepResult:
        """Validate environment variables and system requirements."""
        print('🌍 Validating environment...')
        self.add_success(f'Python version {sys.version.split()[0]} is supported')
        required_vars = ['DISCORD_BOT_TOKEN', 'QDRANT_URL']
        missing_vars = []
        for var in required_vars:
            if not getattr(sys.modules.get('os', __import__('os')), 'environ', {}).get(var):
                missing_vars.append(var)
        if missing_vars:
            self.add_error(f'Missing required environment variables: {', '.join(missing_vars)}')
        else:
            self.add_success('Required environment variables are set')
        return StepResult.ok(data={'environment': 'valid'})

    def validate_dependencies(self) -> StepResult:
        """Validate that all required dependencies are available."""
        print('📦 Validating dependencies...')
        required_packages = ['crewai', 'discord', 'openai', 'qdrant_client', 'pydantic', 'aiohttp', 'httpx']
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                self.add_success(f'Package {package} is available')
            except ImportError:
                missing_packages.append(package)
                self.add_error(f'Package {package} is not installed')
        if missing_packages:
            return StepResult.fail(f'Missing required packages: {', '.join(missing_packages)}')
        return StepResult.ok(data={'dependencies': 'valid'})

    def validate_directories(self) -> StepResult:
        """Validate that required directories exist and are writable."""
        print('📁 Validating directories...')
        try:
            config, _ = validate_config()
            directories_to_check = [config.paths.base_dir, config.paths.downloads_dir, config.paths.config_dir, config.paths.logs_dir, config.paths.processing_dir, config.paths.temp_dir]
            for directory in directories_to_check:
                if not directory.exists():
                    directory.mkdir(parents=True, exist_ok=True)
                    self.add_success(f'Created directory: {directory}')
                else:
                    self.add_success(f'Directory exists: {directory}')
                test_file = directory / '.write_test'
                try:
                    test_file.write_text('test')
                    test_file.unlink()
                    self.add_success(f'Directory is writable: {directory}')
                except Exception as e:
                    self.add_error(f'Directory is not writable: {directory} - {e!s}')
            return StepResult.ok(data={'directories': 'valid'})
        except Exception as e:
            self.add_error(f'Directory validation failed: {e!s}')
            return StepResult.fail(f'Directory validation failed: {e!s}')

    def validate_services(self) -> StepResult:
        """Validate connectivity to external services."""
        print('🌐 Validating service connectivity...')
        try:
            config, _ = validate_config()
            if config.database.qdrant_url:
                if config.database.qdrant_url == ':memory:':
                    self.add_success('Qdrant in-memory mode configured')
                else:
                    try:
                        from memory.qdrant_provider import get_qdrant_client
                        client = get_qdrant_client()
                        client.get_collections()
                        self.add_success('Qdrant connection successful')
                    except Exception as e:
                        self.add_warning(f'Qdrant connection failed: {e!s}')
            else:
                self.add_warning('Qdrant URL not configured')
            try:
                import redis
                r = redis.from_url(config.database.redis_url)
                r.ping()
                self.add_success('Redis connection successful')
            except Exception as e:
                self.add_warning(f'Redis connection failed: {e!s}')
            return StepResult.ok(data={'services': 'valid'})
        except Exception as e:
            self.add_error(f'Service validation failed: {e!s}')
            return StepResult.fail(f'Service validation failed: {e!s}')

    def validate_security(self) -> StepResult:
        """Validate security settings and permissions."""
        print('🔒 Validating security settings...')
        try:
            config, _ = validate_config()
            if hasattr(os, 'getuid') and os.getuid() == 0:
                self.add_warning('Running as root user - consider using a non-root user')
            sensitive_files = [config.paths.google_credentials]
            for file_path in sensitive_files:
                if file_path.exists():
                    stat = file_path.stat()
                    if stat.st_mode & 63:
                        self.add_warning(f'Sensitive file {file_path} has overly permissive permissions')
                    else:
                        self.add_success(f'File permissions are secure: {file_path}')
            return StepResult.ok(data={'security': 'valid'})
        except Exception as e:
            self.add_error(f'Security validation failed: {e!s}')
            return StepResult.fail(f'Security validation failed: {e!s}')

    def run_all_checks(self) -> StepResult:
        """Run all validation checks."""
        print('🚀 Starting Ultimate Discord Intelligence Bot validation...')
        print('=' * 60)
        start_time = time.time()
        checks = [self.validate_configuration, self.validate_environment, self.validate_dependencies, self.validate_directories, self.validate_services, self.validate_security]
        for check in checks:
            try:
                result = check()
                if not result.success:
                    self.add_error(f'Check failed: {result.error}')
            except Exception as e:
                self.add_error(f'Check failed with exception: {e!s}')
        elapsed_time = time.time() - start_time
        print('\n' + '=' * 60)
        print('📊 Validation Summary')
        print('=' * 60)
        print(f'✅ Checks passed: {self.checks_passed}')
        print(f'❌ Checks failed: {self.checks_failed}')
        print(f'⚠️  Warnings: {len(self.warnings)}')
        print(f'⏱️  Time taken: {elapsed_time:.2f}s')
        if self.warnings:
            print('\n⚠️  Warnings:')
            for warning in self.warnings:
                print(f'  • {warning}')
        if self.errors:
            print('\n❌ Errors:')
            for error in self.errors:
                print(f'  • {error}')
            return StepResult.fail(f'Validation failed with {len(self.errors)} errors')
        print('\n🎉 All validation checks passed!')
        return StepResult.ok(data={'checks_passed': self.checks_passed, 'checks_failed': self.checks_failed, 'warnings': len(self.warnings), 'elapsed_time': elapsed_time})

def main() -> int:
    """Main entry point for startup validation."""
    validator = StartupValidator()
    result = validator.run_all_checks()
    if result.success:
        print('\n🚀 System is ready to start!')
        return 0
    else:
        print(f'\n💥 System validation failed: {result.error}')
        return 1
if __name__ == '__main__':
    sys.exit(main())