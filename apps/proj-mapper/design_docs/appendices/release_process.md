# Release Process

**Version:** 1.0.0  
**Last Updated:** 2023-11-05  
**Status:** Draft

## Document Purpose

This document outlines the release process for the Project Mapper system. It defines the procedures, standards, and checkpoints for releasing new versions of the software to ensure quality, consistency, and proper communication with users.

## Release Principles

The Project Mapper release process is guided by the following principles:

1. **Quality First**: Every release must meet defined quality standards
2. **Semantic Versioning**: Version numbers convey meaning about changes
3. **Automation**: Automate as much of the release process as possible
4. **Transparency**: Changes in each release are clearly documented
5. **Backward Compatibility**: Preserve backward compatibility when possible

## Release Types

### Major Releases (X.0.0)

Major releases include significant changes that may break backward compatibility.

**Characteristics:**

- Substantial new features or architectural changes
- Breaking API changes
- Significant user experience changes
- Removal of deprecated features

**Frequency:** Approximately once per year

### Minor Releases (0.X.0)

Minor releases include new features that maintain backward compatibility.

**Characteristics:**

- New features and enhancements
- Non-breaking API additions
- Performance improvements
- Deprecation notices for future breaking changes

**Frequency:** Approximately every 2-3 months

### Patch Releases (0.0.X)

Patch releases include bug fixes and minor improvements that maintain backward compatibility.

**Characteristics:**

- Bug fixes
- Documentation improvements
- Minor performance optimizations
- No API changes

**Frequency:** As needed, typically every 2-4 weeks

### Pre-releases

Pre-release versions allow testing of upcoming changes before official release.

**Types:**

- **Alpha (0.X.0a1)**: Early testing of new features, may have known issues
- **Beta (0.X.0b1)**: Feature complete but may have unknown issues
- **Release Candidate (0.X.0rc1)**: Potential final release pending testing

## Versioning

### Semantic Versioning

Project Mapper follows [Semantic Versioning 2.0.0](https://semver.org/) with the format `MAJOR.MINOR.PATCH[-PRERELEASE]`:

1. **MAJOR** version increments for incompatible API changes
2. **MINOR** version increments for backward-compatible new features
3. **PATCH** version increments for backward-compatible bug fixes
4. **PRERELEASE** identifiers include `a` (alpha), `b` (beta), or `rc` (release candidate) with a number

### Version Representation

Version information is stored and displayed consistently:

- In code: `__version__ = "1.2.3"`
- In package metadata: `version="1.2.3"` in setup.py/pyproject.toml
- In documentation: "Project Mapper 1.2.3"
- In release artifacts: `proj_mapper-1.2.3.tar.gz`

## Release Planning

### Release Roadmap

A public roadmap outlines planned features and target timelines for upcoming releases:

- Major features planned for each release
- Target dates for upcoming releases
- Priority of features and improvements
- Dependencies between features

### AI Agent Compatibility Considerations

Each release must specifically evaluate and document impacts on AI agent consumers:

- Ensure backward compatibility for AI-consumed data structures
- Document any changes to schemas that affect AI parsing
- Include test cases specifically for AI agent consumption patterns
- Version schemas separately from code when needed to maintain AI compatibility
- Provide migration guidance for AI-specific integration points
- Test with actual AI agents to verify compatibility before release
- Include AI-specific release notes highlighting relevant changes

### Feature Tracking

Features are tracked in the issue tracker with appropriate labeling:

- `release-blocker`: Must be addressed before release
- `feature`: New functionality
- `enhancement`: Improvements to existing functionality
- `bug`: Issues that need to be fixed
- `documentation`: Documentation improvements
- Release-specific labels (e.g., `v1.2.0`) to target specific releases

## Release Process Flow

### 1. Release Planning

1. Define the scope of the release
2. Assign issues/features to the release milestone
3. Establish release timeline and key checkpoints
4. Communicate release plans to stakeholders

### 2. Feature Development

1. Implement features in feature branches
2. Review code through pull requests
3. Merge approved changes to the development branch
4. Update documentation for new features
5. Write or update tests for new functionality

### 3. Release Preparation

1. Create a release branch from the development branch
2. Freeze feature development for the release
3. Update version numbers in code and documentation
4. Generate and review release notes
5. Perform final quality checks

### 4. Testing

1. Run the full test suite with coverage
2. Conduct integration and system testing
3. Perform compatibility testing
4. Generate pre-release for broader testing if needed
5. Address any critical issues discovered

### 5. Release Execution

1. Merge the release branch to main
2. Tag the release in version control
3. Build release artifacts
4. Publish to PyPI
5. Update documentation site

### 6. Post-Release

1. Announce the release to users
2. Merge main back to development branch
3. Close completed milestone
4. Review and refine the release process
5. Begin planning the next release

## Release Checklist

### Pre-Release Checklist

- [ ] All tests pass on all supported Python versions
- [ ] Test coverage meets or exceeds target (80%)
- [ ] Documentation is updated and accurate
- [ ] Release notes are complete and accurate
- [ ] Version numbers are updated in all locations
- [ ] All release-blocker issues are resolved
- [ ] Backwards compatibility is maintained (or breaking changes documented)
- [ ] Performance benchmarks meet targets

### Release Execution Checklist

- [ ] Create a release branch (`release-X.Y.Z`)
- [ ] Update version number in `__version__.py`
- [ ] Update version in `pyproject.toml`/`setup.py`
- [ ] Update CHANGELOG.md with release notes
- [ ] Commit version bump (`git commit -m "Bump version to X.Y.Z"`)
- [ ] Tag release version (`git tag vX.Y.Z`)
- [ ] Push to GitHub (`git push origin release-X.Y.Z && git push origin vX.Y.Z`)
- [ ] Build distribution packages (`python -m build`)
- [ ] Verify distribution packages (`twine check dist/*`)
- [ ] Upload to PyPI (`twine upload dist/*`)
- [ ] Merge release branch to main (`git checkout main && git merge release-X.Y.Z`)
- [ ] Push to GitHub (`git push origin main`)
- [ ] Create GitHub release with release notes
- [ ] Merge main back to development (`git checkout develop && git merge main`)

### Post-Release Checklist

- [ ] Update documentation website
- [ ] Announce release on channels (GitHub, Twitter, blog, etc.)
- [ ] Close milestone in issue tracker
- [ ] Review and address any immediate feedback
- [ ] Start planning next release

## Release Artifacts

The following artifacts are generated and published with each release:

1. **Source Distribution**: `proj_mapper-X.Y.Z.tar.gz`
2. **Wheel Distribution**: `proj_mapper-X.Y.Z-py3-none-any.whl`
3. **Documentation**: Updated documentation on ReadTheDocs
4. **Release Notes**: Detailed changelog in Markdown format
5. **GitHub Release**: Tagged release with release notes and assets

## Release Automation

The release process is automated using GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine wheel
      - name: Build package
        run: python -m build
      - name: Verify package
        run: twine check dist/*
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@master
        with:
          user: __token__
          password: ${{ secrets.PYPI_API_TOKEN }}
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Release Notes

### Format

Release notes follow a consistent format:

```markdown
# Project Mapper 1.2.0

Release Date: 2023-11-05

## Summary

Brief description of the release highlights.

## New Features

- Feature 1: Description (#123)
- Feature 2: Description (#124)

## Enhancements

- Enhancement 1: Description (#125)
- Enhancement 2: Description (#126)

## Bug Fixes

- Fixed issue where X would occur when Y (#127)
- Resolved error in Z functionality (#128)

## Documentation

- Added guide for feature X (#129)
- Improved examples for Y (#130)

## Breaking Changes

- Change 1: Description and migration path (#131)

## Deprecations

- Feature X will be removed in version 2.0.0 (#132)

## Internal Changes

- Refactored component X for better maintainability (#133)
- Improved test coverage for module Y (#134)

## Contributors

Thanks to the following contributors for this release:
@username1, @username2, @username3
```

### Changelog Maintenance

The CHANGELOG.md file is maintained in the repository and updated with each release:

- Unreleased changes are tracked in an "Unreleased" section
- During release, the "Unreleased" section is renamed to the release version
- Each entry links to the relevant issue or pull request
- Breaking changes are clearly highlighted
- Migration guidance is provided for breaking changes

## Communication Plan

### Pre-Release Communication

Before a significant release:

1. Announce upcoming features on GitHub Discussions
2. Share release timeline with estimated dates
3. Request early feedback on major changes
4. Highlight breaking changes and migration paths

### Release Announcement

When a release is published:

1. Post detailed release notes on GitHub Releases
2. Update documentation with new features and examples
3. Send announcement to mailing list (if applicable)
4. Share on social media channels

### Post-Release Support

After a release:

1. Monitor issues for bugs related to the new release
2. Address critical issues with patch releases
3. Collect feedback for future improvements
4. Update FAQs based on common questions

## Long-Term Support

### Support Policy

- Each major version is supported for 12 months after the next major version is released
- Only the latest minor version of each major version receives regular updates
- Critical security fixes may be backported to older supported versions
- End-of-life dates for versions are published in advance

### Compatibility Policy

- Breaking changes are only introduced in major releases
- Deprecated features are marked with warnings at least one minor release before removal
- Migration guides are provided for all breaking changes
- Python version compatibility is clearly documented

## Related Documents

- [Coding Standards](coding_standards.md)
- [Testing Strategy](testing_strategy.md)
- [System Architecture](../architecture/system_architecture.md)
- [Functional Requirements](../requirements/functional_requirements.md) - See section FR-7 for AI Development and Maintenance Support
- [Non-Functional Requirements](../requirements/non_functional_requirements.md) - See sections AI-1 through AI-5 for AI Consumption Requirements

---

_End of Release Process Document_
