# End Development Session

Complete the current session with comprehensive documentation.

## Wrap-up Tasks

1. **Final Status Check**:
   ```bash
   git status
   git diff --stat
   ```

2. **Run Final Tests**:
   - Execute test suite
   - Note any failures for next session
   - Check linting/formatting

3. **Update Session Document** with:

   ### Summary Section
   - What was accomplished
   - What remains incomplete
   - Time spent (approximate)
   - Lines of code changed

   ### Technical Details
   - Key code changes made
   - Design decisions and rationale
   - Performance considerations
   - Security considerations

   ### Problems Encountered
   - Issues faced and solutions
   - Workarounds implemented
   - External blockers

   ### Knowledge Captured
   - New patterns learned
   - Useful commands discovered
   - Documentation gaps found
   - Tool configurations

   ### Handoff Notes
   - Current state of work
   - Next logical steps
   - Any WIP code explained
   - Testing status

4. **Commit Work**:
   ```bash
   git add -A
   git commit -m "checkpoint: session end - [brief summary]"
   ```

5. **Update Project Docs**:
   - Update TODO.md if exists
   - Note in README if major changes
   - Update CHANGELOG if applicable

6. **Store Session**:
   - Save final session document
   - Update `.claude/sessions/index.md` with session link
   - Note session highlights for future reference

## Final Output

Provide:
1. Session duration and productivity metrics
2. Bullet-point summary of achievements
3. Clear next steps for continuation
4. Any blockers that need resolution
5. Session file location for future reference
