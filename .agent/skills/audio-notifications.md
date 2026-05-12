# Skill: Audio Notifications

## Description

This skill manages audio notifications for task completion events. When an agent completes a workflow, the appropriate audio file is played to notify the user that the task has finished and what type of task it was.

## Audio Files Location

All audio files are stored in: `.agent/assets/audios/`

## Audio Mapping

Each workflow completion triggers a specific audio file:

| Workflow Code | Workflow Name | Audio File | Description |
|---------------|---------------|-------------|-------------|
| `WORK` | `implement-issue.md` | `Issue solucionada.mp3` | Played when an issue is implemented and moved to done |
| `TEST` | `prueba-el-proyecto.md` | `Prueba Completada.mp3` | Played when black-box project testing completes |
| `TEST-PYPI` | `test-project-pypi.md` | `Prueba desde PyPi.mp3` | Played when PyPI-based testing completes |
| `COMMIT` | `commit-push.md` | `Commit subido.mp3` | Played when changes are committed and pushed |
| `DOCS` | `update-documentation.md` | `Documentacion actualizada.mp3` | Played when documentation sync completes |
| `HISTORY` | `daily-log.md` | `Historial Actualizado.mp3` | Played when daily log is updated |
| `FIND` | `convert-findings-to-issues.md` | `de find a issues.mp3` | Played when findings are converted to issues |
| `SETUP` | `project-setup.md` | `tarea general terminada.mp3` | Played when project setup completes |
| `ISSUE` | `create-issue.md` | `tarea general terminada.mp3` | Played when new issues are created |

## Playback Command

To play an audio notification without opening an external player, use the provided script:

**Windows (Recommended - using MCI API):**
```python
import sys
sys.path.insert(0, '.agent/assets')
from play_audio import play_audio

# Example: Play "tarea general terminada.mp3"
audio_path = os.path.join('.agent', 'assets', 'audios', 'tarea general terminada.mp3')
play_audio(audio_path, wait=True)
```

**Command line usage:**
```bash
.venv/Scripts/python.exe .agent/assets/play_audio.py ".agent/assets/audios/Issue solucionada.mp3"
```

**Alternative (opens default player):**
```python
import os
os.startfile('.agent/assets/audios/Issue solucionada.mp3')
```

## Usage in Workflows

At the end of each workflow, after completing all steps:

1. Identify the workflow code from the Audio Mapping table
2. Select the corresponding audio file
3. Execute the playback command

## Workflow Integration

Each workflow in `.agent/workflows/` should include an audio notification section at the end. The workflow should reference this skill for the correct audio file to play.

### Example Integration in Workflow

At the end of `implement-issue.md`, add:

```markdown
---

## Audio Notification

See `.agent/skills/audio-notifications.md` for audio playback.
**Audio**: `Issue solucionada.mp3`
```

## Important Notes

1. **ALWAYS play audio at workflow completion**: Never skip audio notification
2. **Use correct audio file**: Match the workflow to the correct audio per the mapping table
3. **Use absolute path**: Recommended method is `os.startfile()` with absolute path to avoid path resolution issues
4. **Non-blocking**: `os.startfile()` is non-blocking - audio plays in background. Use PowerShell `PlaySync()` for blocking playback if needed.

## Fallback for General Tasks

When the user gives the agent a direct instruction that is NOT one of the predefined workflows (e.g., "analyze this code", "check the status", "run a specific command", etc.), use the **fallback audio**:

**Audio**: `tarea general terminada.mp3`

This audio is played when:
- The agent completes a task given directly by the user
- The task does not match any predefined workflow in the Audio Mapping table
- The task is a one-off operation or ad-hoc request

### Decision Logic

```
IF task matches a predefined workflow → Use specific audio from mapping table
ELSE → Use "tarea general terminada.mp3" (fallback)
```

## Related Skills

- [terminal.md](./terminal.md) - Terminal commands for audio playback
- [issue-driven-development.md](./issue-driven-development.md) - Issue workflow
- [project-testing.md](./project-testing.md) - Testing workflow