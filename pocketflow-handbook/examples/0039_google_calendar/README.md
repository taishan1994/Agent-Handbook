# Pocket Google Calendar

An application based on the Pocket Flow framework for Google Calendar integration.

## 📋 Description

This project implements a Google Calendar integration using the Pocket Flow framework, allowing efficient management of events and appointments through a simple and intuitive interface.

## 🚀 Features

- Google Calendar API Integration
- Event Management
- Appointment Viewing
- Flow-based Interface using Pocket Flow

## 🛠️ Technologies Used

- Python
- Pocket Flow Framework
- Google Calendar API
- Pipenv for dependency management

## 📦 Installation

1. Clone the repository:
```bash
git clone [REPOSITORY_URL]
cd pocket-google-calendar
```

2. Install dependencies using Pipenv:
```bash
pipenv install
```

## 🔑 Credentials Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API for your project
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application" as the application type
   - Download the credentials file
   - Rename it to `credentials.json`
   - Place it in the root directory of the project

## 🌍 Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Google Calendar API Configuration
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com
GOOGLE_APPLICATION_CREDENTIALS=credentials.json

# Application Configuration
TIMEZONE=America/Sao_Paulo  # or your preferred timezone
```

## 🔧 Configuration

1. Activate the virtual environment:
```bash
pipenv shell
```

2. Run the application:
```bash
python main.py
```

## Expected Output

When running the example, you'll see an output similar to this:

```
=== Listing your calendars ===
- Primary Calendar
- Work
- Personal

=== Creating an example event ===
Event created successfully!
Event ID: abc123xyz
```


## 📁 Project Structure

```
pocket-google-calendar/
├── main.py           # Application entry point
├── nodes.py          # Pocket Flow node definitions
├── utils/            # Utilities and helper functions
├── Pipfile           # Pipenv configuration
├── credentials.json  # Google Calendar API credentials
├── .env             # Environment variables
└── token.pickle      # Google Calendar authentication token
```

## 🤝 Contributing

1. Fork the project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is under the MIT License. See the [LICENSE](LICENSE) file for more details.

## ✨ Acknowledgments

- [Pocket Flow](https://github.com/the-pocket/PocketFlow) - Framework used
- [Google Calendar API](https://developers.google.com/calendar) - Integration API 