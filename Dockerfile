# Dockerfile for jesse-mcp in MetaMCP
FROM metamcp:latest

# Copy the jesse-mcp source code
COPY . /app/jesse-mcp
WORKDIR /app/jesse-mcp

# Install runtime dependencies
RUN pip install -q -r requirements.txt

# Install the package in development mode (for easy updates)
RUN pip install -e .

# Verify installation
RUN jesse-mcp --version

# The entry point is configured via setup.py
# MetaMCP will call: jesse-mcp (via console_scripts entry point)