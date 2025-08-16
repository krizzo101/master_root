# PROJECT DIRECTIVES

## File Management Rules (ALL FILES)

### APPLIES TO: Code, Documentation, Configuration, Scripts, Tests - EVERYTHING
1. **UPDATE existing files** - Do not create duplicate versions
2. **NO versioning in filenames** - No "v2", "verified", "final", "updated", "new", "fixed" suffixes
3. **Single source of truth** - One file per purpose
4. **Fix in place** - Correct errors in the original file
5. **No parallel versions** - Never have multiple versions of the same functionality
6. **USE GIT FOR VERSIONING** - Commit changes regularly with descriptive messages

### Git Commit Requirements
- **COMMIT FREQUENTLY** - After completing each logical unit of work
- **Check git status regularly** - Use `git status` before and after changes
- **Descriptive messages** - Explain what changed and why
- **Atomic commits** - Each commit should be a single logical change
- **Never rely on filenames for versioning** - That's what git is for
- **Commit at least**:
  - After fixing errors in existing files
  - After completing documentation updates
  - After implementing new features
  - After significant refactoring
  - Before switching to different tasks

### Quality Standards
- All content must be tested and accurate
- Do not document/code assumptions or guesses as facts
- If something is untested, mark it as "NOT TESTED"
- Do not add meta-commentary about verification or corrections
- No comments about "fixing" or "updating" previous versions