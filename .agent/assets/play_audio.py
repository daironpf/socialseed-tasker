"""
Audio playback module using Windows MCI (Media Control Interface).
Plays MP3 files without opening an external player.
"""
import os
import ctypes
from ctypes import wintypes

# Windows MCI constants
MCI_OPEN = 0x0803
MCI_PLAY = 0x0806
MCI_CLOSE = 0x0804
MCI_WAIT = 0x0004
MCI_FROM = 0x00000002

class AudioPlayer:
    def __init__(self):
        self.device_id = None
        self.mci = ctypes.windll.winmm.mciSendStringW
        self.mci_error = ctypes.windll.winmm.mciGetErrorStringW

    def open(self, file_path: str) -> bool:
        """Open an audio file."""
        absolute_path = os.path.abspath(file_path)
        command = f'open "{absolute_path}" alias audio_file'
        error = self.mci(command, None, 0, None)
        if error:
            error_msg = self._get_error(error)
            print(f"Failed to open audio: {error_msg}")
            return False
        return True

    def play(self) -> bool:
        """Play the loaded audio."""
        error = self.mci("play audio_file", None, 0, None)
        if error:
            error_msg = self._get_error(error)
            print(f"Failed to play audio: {error_msg}")
            return False
        return True

    def play_and_wait(self) -> bool:
        """Play the audio and wait for completion."""
        error = self.mci("play audio_file wait", None, MCI_WAIT, None)
        if error:
            error_msg = self._get_error(error)
            print(f"Failed to play audio: {error_msg}")
            return False
        return True

    def close(self) -> bool:
        """Close the audio device."""
        if self.device_id is None:
            return True
        error = self.mci("close audio_file", None, 0, None)
        return error == 0

    def _get_error(self, error_code):
        """Get error message for MCI error code."""
        buffer = ctypes.create_unicode_buffer(256)
        self.mci_error(error_code, buffer, 256)
        return buffer.value


def play_audio(file_path: str, wait: bool = True) -> bool:
    """
    Play an audio file.

    Args:
        file_path: Path to the audio file (MP3, WAV, etc.)
        wait: If True, wait for playback to finish. If False, return immediately.

    Returns:
        True if successful, False otherwise.
    """
    player = AudioPlayer()

    if not player.open(file_path):
        return False

    if wait:
        result = player.play_and_wait()
    else:
        result = player.play()

    player.close()
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python play_audio.py <audio_file.mp3>")
        sys.exit(1)

    audio_file = sys.argv[1]
    print(f"Playing: {audio_file}")
    success = play_audio(audio_file, wait=True)
    sys.exit(0 if success else 1)