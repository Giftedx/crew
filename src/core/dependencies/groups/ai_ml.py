"""AI/ML dependency group definitions."""

# Core AI/ML dependencies
AI_ML_GROUP: set[str] = {
    "numpy",
    "pandas",
    "scikit-learn",
    "torch",
    "transformers",
    "tokenizers",
    "accelerate",
    "datasets",
    "evaluate",
    "huggingface_hub",
}

# Optional AI/ML dependencies
AI_ML_OPTIONAL: set[str] = {
    "tensorflow",
    "jax",
    "flax",
    "optimum",
    "sentence-transformers",
    "spacy",
    "nltk",
    "openai",
    "anthropic",
    "cohere",
    "together",
    "replicate",
}

# Development AI/ML dependencies
AI_ML_DEV: set[str] = {
    "wandb",
    "tensorboard",
    "mlflow",
    "neptune",
    "optuna",
    "hyperopt",
    "ray",
    "dask",
}
