import pytest
import typer.testing

import ignoro.api as api


@pytest.fixture(scope="function")
def runner() -> typer.testing.CliRunner:
    return typer.testing.CliRunner(mix_stderr=False)


@pytest.fixture(scope="function")
def templates() -> api.Templates:
    return api.Templates()


@pytest.fixture(scope="session")
def mock_template_names() -> list[str]:
    return [
        "c",
        "c#",
        "c++",
        "django",
        "go",
        "java",
        "javascript",
        "php",
        "python",
        "ruby",
        "rust",
        "swift",
        "typescript",
    ]


@pytest.fixture(scope="session")
def mock_template_go() -> str:
    return """# Created by https://www.toptal.com/developers/gitignore/api/go
# Edit at https://www.toptal.com/developers/gitignore?templates=go

### Go ###
# If you prefer the allow list template instead of the deny list, see community template:
# https://github.com/github/gitignore/blob/main/community/Golang/Go.AllowList.gitignore
#
# Binaries for programs and plugins
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary, built with `go test -c`
*.test

# Output of the go coverage tool, specifically when used with LiteIDE
*.out

# Dependency directories (remove the comment below to include it)
# vendor/

# Go workspace file
go.work

# End of https://www.toptal.com/developers/gitignore/api/go"""


@pytest.fixture(scope="session")
def mock_template_ruby() -> str:
    return """# Created by https://www.toptal.com/developers/gitignore/api/ruby
# Edit at https://www.toptal.com/developers/gitignore?templates=ruby

### Ruby ###
*.gem
*.rbc
/.config
/coverage/
/InstalledFiles
/pkg/
/spec/reports/
/spec/examples.txt
/test/tmp/
/test/version_tmp/
/tmp/

# Used by dotenv library to load environment variables.
# .env

# Ignore Byebug command history file.
.byebug_history

## Specific to RubyMotion:
.dat*
.repl_history
build/
*.bridgesupport
build-iPhoneOS/
build-iPhoneSimulator/

## Specific to RubyMotion (use of CocoaPods):
#
# We recommend against adding the Pods directory to your .gitignore. However
# you should judge for yourself, the pros and cons are mentioned at:
# https://guides.cocoapods.org/using/using-cocoapods.html#should-i-check-the-pods-directory-into-source-control
# vendor/Pods/

## Documentation cache and generated files:
/.yardoc/
/_yardoc/
/doc/
/rdoc/

## Environment normalization:
/.bundle/
/vendor/bundle
/lib/bundler/man/

# for a library or gem, you might want to ignore these files since the code is
# intended to run in multiple environments; otherwise, check them in:
# Gemfile.lock
# .ruby-version
# .ruby-gemset

# unless supporting rvm < 1.11.0 or doing something fancy, ignore this:
.rvmrc

# Used by RuboCop. Remote config files pulled in from inherit_from directive.
# .rubocop-https?--*

# End of https://www.toptal.com/developers/gitignore/api/ruby"""
