# Product Recommendation ChatBot 🛍️

A smart chatbot assistant that helps users find product recommendations based on Flipkart product reviews and ratings.

## 🌟 Features

- Interactive chat interface
- Product recommendations based on user queries
- Review analysis and summarization
- Rating-based filtering
- Real-time responses
- Mobile-responsive design

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: Astra DB (Vector Store)
- **LLM Integration**: Groq
- **Vector Embeddings**: HuggingFace
- **Dependencies**: LangChain, Pandas

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Anaconda/Miniconda (recommended)
- Groq API key
- Astra DB account
- HuggingFace API token

### Environment Setup

1. **Create and Activate Conda Environment**:
```bash
# Create environment
conda create -p <env_name> python=3.10 -y

# Activate environment
conda activate <env_path>

# For bash terminal
source activate ./<env_name>
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install Local Package**:
```bash
python setup.py install
```

### Configuration

Create a `.env` file in the root directory with the following variables:
```env
GROQ_API_KEY = "your_groq_api_key"
ASTRA_DB_API_ENDPOINT = "your_astra_db_endpoint"
ASTRA_DB_APPLICATION_TOKEN = "your_astra_db_token"
ASTRA_DB_KEYSPACE = "your_keyspace"
HF_TOKEN = "your_huggingface_token"
```

## 📂 Project Structure

```
flipkart/
├── flipkart/
│   ├── data_converter.py    # Data processing
│   ├── data_ingestion.py    # Database operations
│   └── retrieval_generation.py  # Chat logic
├── static/
│   └── style.css           # UI styling
├── templates/
│   ├── chat.html          # Chat interface
│   ├── 404.html          # Error pages
│   └── 500.html
├── app.py                # Flask application
└── requirements.txt      # Dependencies
```

## 🚀 Running the Application

1. **Start the Flask Server**:
```bash
python app.py
```

2. **Access the Application**:
- Open your browser and navigate to `http://localhost:5000`
- Start chatting with the assistant!

## 💬 Usage Examples

- "Can you recommend headphones with good bass?"
- "What are the best budget earphones?"
- "Show me reviews for BoAt Rockerz"

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

- **Yunus Shaikh**
- Email: syunus838@gmail.com

## 🙏 Acknowledgments

- Flipkart for the product dataset
- Groq for LLM API access
- DataStax for Astra DB
- HuggingFace for embeddings

## 📞 Support

For support, email syunus838@gmail.com or open an issue in the repository.

