# NexBack

NexBack is a Dual N-Back cognitive training application built with Python and PyQt6.

## Features (MVP)

- **Dual N-Back Training**: Tracks both spatial position and auditory letters.
- **Configurable N-Level**: Default is N=2.
- **Real-time Feedback**: Visual indicators for Hits, Misses, and False Alarms.
- **Scoring System**: Tracks performance for both modalities.

## Installation

1. Ensure you have Python 3.13+ installed.
2. Install dependencies:

   ```bash
   pip install .
   ```

   Or manually:

   ```bash
   pip install PyQt6
   ```

## Running the Application

```bash
python main.py
```

## Controls

- **Start Session**: Click the "Start Session" button.
- **Position Match**: Press **'A'** when the current square position matches the one N steps ago.
- **Audio Match**: Press **'L'** when the current spoken letter matches the one N steps ago.
