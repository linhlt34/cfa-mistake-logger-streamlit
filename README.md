# CFA Mistake Logger



A Streamlit application for tracking and analyzing mistakes made during CFA exam practice questions.



## Features



- **Automatic Text Parsing**: Extracts question details, results, and categories from pasted content

- **Error Classification**: Categorize mistakes into different types:

  - Misread the question

  - Wrong formula/concept

  - Calculation error  

  - Uncertain

- **Notes Support**: Add detailed notes for each mistake

- **Data Export**: Export mistake log to CSV with timestamp

- **Data Import**: Load and merge existing CSV logs

- **Real-time Display**: View recent mistakes in a clean table format



## Installation



1. Clone this repository:

```bash

git clone <your-repo-url>

cd cfa_logerror

```



2. Create a virtual environment:

```bash

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

```



3. Install dependencies:

```bash

pip install -r requirements.txt

```



## Usage



### Local Development



1. Run the application:

```bash

streamlit run app.py

```



2. Open your browser and navigate to `http://localhost:8501`



### Streamlit Cloud Deployment



This app is ready for deployment on Streamlit Cloud:



1. Push your code to GitHub

2. Go to [share.streamlit.io](https://share.streamlit.io)

3. Connect your GitHub repository

4. Deploy with main file: `app.py`



### Using the App



1. Paste your CFA question content into the text area

2. Select the appropriate error type to automatically save the entry

3. Add optional notes for additional context

4. View your mistake history in the table below

5. Export your data or load previous logs as needed



## Data Structure



The application tracks the following information for each mistake:



- **Category**: Subject area (e.g., Time-Series Analysis)

- **Question Number**: Question identifier (e.g., "3 of 73")

- **Result**: Correct/Incorrect/Uncertain

- **Question Text**: The actual question content

- **Error Type**: Classification of the mistake

- **Notes**: Optional additional observations

- **Timestamp**: When the mistake was logged



## Contributing



1. Fork the repository

2. Create a feature branch

3. Make your changes

4. Submit a pull request



## License



This project is open source and available under the MIT License.

# cfa-mistake-logger-streamlit