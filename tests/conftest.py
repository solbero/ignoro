import pytest
import typer.testing

import ignoro.api as api


@pytest.fixture(scope="function")
def runner() -> typer.testing.CliRunner:
    return typer.testing.CliRunner()


@pytest.fixture(scope="function")
def templates() -> api.TemplateList:
    return api.TemplateList()


@pytest.fixture(scope="session")
def template_names() -> list[str]:
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
def template_content() -> str:
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
