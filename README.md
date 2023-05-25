# YouTube Data Analyzer

This tool extracts details about YouTube channels and videos using Google's YouTube Data API v3 and stores the information in a PostgreSQL database for further analysis. The details include channel IDs, video IDs, video titles, upload dates, view counts, like counts, and comment counts.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.x
- Pip (Python package manager)
- PostgreSQL server

### Installing

1. Clone the repository to your local machine:

```bash
git clone https://github.com/byronabyrd/youtube-data-analyzer.git
```

2. Navigate into the project directory:

```bash
cd youtube-data-analyzer
```

3. Install the necessary Python packages:

```bash
pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib google-auth-httplib2 google-auth-oauthlib requests pandas psycopg2 sqlalchemy
```

## Usage

Before running the script, make sure to set up the following environment variables:
- `API_KEY`: your Google API key
- `DB_NAME`: your PostgreSQL database name
- `DB_USERNAME`: your PostgreSQL username
- `DB_PASSWORD`: your PostgreSQL password
- `DB_HOST`: your PostgreSQL host
- `DB_PORT`: your PostgreSQL port

To run the script, navigate to the directory containing the script and type the following command:

```bash
python script_name.py
```

## Built With

- [Python](https://www.python.org/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [PostgreSQL](https://www.postgresql.org/)

## Contributing

Please read [CONTRIBUTING.md](https://github.com/byronabyrd/youtube-data-analyzer/blob/main/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/byronabyrd/youtube-data-analyzer/blob/main/LICENSE.md) file for details

---

Don't forget to replace `yourusername` with your actual GitHub username and `script_name.py` with your actual Python script's name.

Please keep in mind that it's always a good idea to provide detailed comments in your code as well. This will make your project more understandable and accessible to other developers who might be interested in using or contributing to your project.
