# Publishing Guide for django-api-mixins

This guide will walk you through publishing your package to PyPI.

## Prerequisites

1. **PyPI Account**: Create an account at [pypi.org](https://pypi.org/account/register/)
2. **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org/account/register/) (for testing)

## Step 1: Update Package Information

Before publishing, update the following in `pyproject.toml`:

1. **Author Information**: Update the `authors` field with your name and email
2. **Package Name**: Check if `django-api-mixins` is available on PyPI. If not, choose a different name
3. **URLs**: Update the `project.urls` section with your actual GitHub repository URLs (if applicable)
4. **Version**: Start with `0.1.0` for the first release

## Step 2: Install Build Tools

```bash
pip install build twine
```

## Step 3: Build the Package

```bash
# From the project root directory
python -m build
```

This will create:
- `dist/django-api-mixins-0.1.0.tar.gz` (source distribution)
- `dist/django_api_mixins-0.1.0-py3-none-any.whl` (wheel distribution)

## Step 4: Test on TestPyPI (Recommended)

### Upload to TestPyPI

**Option 1: Using API Token (Recommended)**

```bash
twine upload --repository testpypi --username __token__ --password pypi-AgENdGVzdC5weXBpLm9yZwIkOWYxZjcxYjQtMGVjNi00MmM5LTk1ZWUtNGFjNzVjY2Y2MWIxAAIqWzMsImEzZGI3Y2IwLWMyMjctNDQ4Yy1iZGM4LWVlYmVmMzBlMjZkYiJdAAAGIN-40-Pz1BXNErq5nl3LG7gl_u-B407IIQlaeRz9_lYQ dist/*
```

**Option 2: Interactive (when prompted)**

```bash
twine upload --repository testpypi dist/*
```

When prompted:
- **Username**: Enter exactly `__token__` (with double underscores)
- **Password**: Paste your full token including the `pypi-` prefix

**Important Notes:**
- The username must be exactly `__token__` (not your actual username)
- Copy the entire token including the `pypi-` prefix
- Make sure there are no extra spaces or newlines when pasting
- If you get a 403 error, try Option 1 (command line) to avoid copy-paste issues

### Test Installation from TestPyPI

**Important**: TestPyPI doesn't have all packages, so you need to use `--extra-index-url` to allow pip to find dependencies (Django, djangorestframework) from the main PyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ django-api-mixins
```

Or create a test virtual environment:

```bash
python -m venv test_env
test_env\Scripts\activate  # On Windows
# source test_env/bin/activate  # On Linux/Mac

pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ django-api-mixins
```

**Note**: Make sure you've successfully uploaded the package to TestPyPI first. If you get "Package not found", verify the upload was successful by checking https://test.pypi.org/project/django-api-mixins/

## Step 5: Publish to PyPI

**Important**: Production PyPI requires a **separate API token** from TestPyPI. You cannot use your TestPyPI token for production PyPI.

### Create a Production PyPI API Token

1. Go to [pypi.org/manage/account/](https://pypi.org/manage/account/)
2. Scroll down to "API tokens" section
3. Click "Add API token"
4. Give it a name (e.g., "django-api-mixins-upload")
5. Set scope to "Entire account" (or just the project if you prefer)
6. Click "Add token"
7. **Copy the token immediately** - it starts with `pypi-` and you won't be able to see it again!

### Upload to Production PyPI

**Option 1: Using API Token (Recommended)**

```bash
twine upload --username __token__ --password YOUR_PRODUCTION_PYPI_TOKEN dist/*
```

Replace `YOUR_PRODUCTION_PYPI_TOKEN` with the token you just created.

**Option 2: Interactive (when prompted)**

```bash
twine upload dist/*
```

When prompted:
- **Username**: Enter exactly `__token__` (with double underscores)
- **Password**: Paste your production PyPI token (starts with `pypi-`)

**Important Notes:**
- Production PyPI token is different from TestPyPI token
- The username must be exactly `__token__` (not your actual username)
- Copy the entire token including the `pypi-` prefix
- Make sure there are no extra spaces or newlines when pasting

## Step 6: Verify Publication

1. Visit `https://pypi.org/project/django-api-mixins/` (or your package name)
2. Verify the package information is correct
3. Test installation: `pip install django-api-mixins`

## Updating the Package

For future releases:

1. **Update version** in `pyproject.toml` (e.g., `0.1.0` → `0.1.1` or `0.2.0`)
2. **Update version** in `src/__init__.py`
3. **Build again**: `python -m build`
4. **Upload**: `twine upload dist/*`

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Troubleshooting

### Package name already exists
- Choose a different name in `pyproject.toml`
- Consider adding your username as prefix (e.g., `yourname-django-api-mixins`)

### Upload fails with authentication error
- Check your username and password
- Use API token instead of password
- Make sure you're using the correct PyPI account

### Import errors after installation
- Verify `src/__init__.py` exports all necessary classes
- Check that relative imports are correct
- Test locally: `pip install -e .` (editable install)

## Additional Resources

- [PyPI Packaging Guide](https://packaging.python.org/en/latest/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
