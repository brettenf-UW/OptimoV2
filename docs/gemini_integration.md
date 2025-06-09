# Gemini Integration Guide

This guide explains how Google's Gemini 2.0 Flash model is used as the AI registrar agent in OptimoV2.

## Configuration

The system is configured to use Gemini as the AI provider in `config/settings.yaml`:

```yaml
pipeline:
  ai_provider: "gemini"
```

## API Key Setup

### Environment Variable

Set the Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

### Command-line Argument

Pass the API key directly:

```bash
python scripts/run_pipeline.py --api-key "your-gemini-api-key-here"
```

## Gemini-Specific Settings

The Gemini integration uses the following settings in `config/settings.yaml`:

```yaml
gemini:
  model: "gemini-2.0-flash"    # Model name
  max_tokens: 2000              # Maximum output tokens
  temperature: 0.1              # Low for consistent decisions
  top_p: 0.1                    # Nucleus sampling parameter
  top_k: 1                      # Top-k sampling parameter
```

## API Details

The Gemini integration uses the REST API endpoint:
- Base URL: `https://generativelanguage.googleapis.com/v1beta/models`
- Model: `gemini-2.0-flash`
- Method: `generateContent`

## Usage Examples

```bash
# Run with test data
python scripts/run_pipeline.py --generate-test-data small

# Run with your own data
python scripts/run_pipeline.py --input-dir /path/to/your/csv/files

# Run with API key as argument
python scripts/run_pipeline.py --api-key "your-key-here" --generate-test-data medium
```

## Troubleshooting

1. **API Key Issues**: Ensure your Gemini API key is valid and has the necessary permissions.

2. **Rate Limits**: If you encounter rate limit errors, consider adjusting the `max_iterations` in the configuration.

3. **Response Format**: The agent expects a specific JSON response format for optimization actions (SPLIT, MERGE, ADD, REMOVE).

## Performance Notes

Gemini 2.0 Flash provides:
- Fast response times
- Consistent decision-making with low temperature settings
- Clear reasoning explanations for each action

Monitor the `registrar_actions.json` files in each iteration to review the AI's decisions and reasoning.