#!/bin/bash

# Create modular jessegpt.md structure from original file
jessegpt_file="jessegpt.md"
output_dir="/home/bk/source/jesse-mcp/jessegpt_modular"

# Extract sections using simpler sed commands
{
  echo "# Jesse MCP Specialized Agent System Prompt"
  echo ""
  echo "You are a specialized assistant with three domain-expert roles for the Jesse trading platform:"
  echo ""
  echo "## Your Core Roles"
  echo ""
  echo "### 1. **Strategy Optimization Expert**"
  # Extract lines 7-13, clean formatting
  sed -n '7,13p' "$jessegpt_file" | sed 's/^/### /1. /' | sed 's/^/### //1. /'
  echo ""
  echo "### 2. **Risk Management Expert**"
  # Extract lines 15-21
  sed -n '15,21p' "$jessegpt_file" | sed 's/^/### /2. /' | sed 's/^/### //2. /'
  echo ""
  echo "### 3. **Backtesting & Analysis Expert**"
  # Extract lines 23-29
  sed -n '23,29p' "$jessegpt_file" | sed 's/^/### /3. /' | sed 's/^/### //3. /'
  echo ""
  echo "## Your Communication Style"
  # Extract lines 31-38
  sed -n '31,38p' "$jessegpt_file" | sed 's/^/## /& /' | sed 's/^/## //& /'
  echo ""
  echo "## Output Format"
  # Extract lines 40-46
  sed -n '40,46p' "$jessegpt_file" | sed 's/^/## /& /' | sed 's/^/## //& /'
  echo ""
  echo "Here are some syntax knowledge and tools of Jesse you should know:"
  echo ""
  # Extract utils section (lines 49-86)
  sed -n '49,86p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract debugging section (lines 102-103)
  sed -n '102,103p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  echo "## Jesse Framework Documentation"
  echo "## Some strategy properties and methods"
  # Extract properties section (lines 847-1413)
  sed -n '847,1413p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract workflow section (lines 217-234)
  sed -n '217,234p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract hyperparameters section (lines 181-210)
  sed -n '181,210p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract DNA usage section (lines 217-234)
  sed -n '217,234p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract properties section (lines 268-353)
  sed -n '268,353p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract examples section (lines 354-506)
  sed -n '354,506p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract first example (lines 417-526)
  sed -n '417,526p' "$jessegpt_file" | sed 's/^/=== Strategy example #1:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract communication style (lines 527-537)
  sed -n '527,537p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract final optimization notes (lines 538-554)
  sed -n '538,554p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract strategy workflow (lines 565-603)
  sed -n '565,603p' "$jessegpt_file" | sed 's/^/# /& /' | sed 's/^/# //& /'
  echo ""
  # Extract second example (lines 604-713)
  sed -n '604,713p' "$jessegpt_file" | sed 's/^/=== Strategy example #2:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract watch list example (lines 714-773)
  sed -n '714,773p' "$jessegpt_file" | sed 's/^/=== Strategy example #3:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract third example (lines 774-834)
  sed -n '774,834p' "$jessegpt_file" | sed 's/^/=== Strategy example #4:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract fourth example (lines 835-896)
  sed -n '835,896p' "$jessegpt_file" | sed 's/^/=== Strategy example #5:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract fifth example (lines 897-958)
  sed -n '897,958p' "$jessegpt_file" | sed 's/^/=== Strategy example #6:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract sixth example (lines 959-1019)
  sed -n '959,1019p' "$jessegpt_file" | sed 's/^/=== Strategy example #7:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract seventh example (lines 1020-1080)
  sed -n '1020,1080p' "$jessegpt_file" | sed 's/^/=== Strategy example #8:/=== /' | sed 's/^/=== //=== /'
  echo ""
  # Extract eighth example (lines 1081-1141)
  sed -n '1081,1141p' "$jessegpt_file" | sed 's/^/=== Strategy example #8:/=== /' | sed 's/^/=== //=== /'
  echo ""
} > "$output_dir"

echo "✅ Modular jessegpt.md created at $output_dir"
echo ""
echo "📋 Content Overview:"
echo "- Core Roles (Strategy, Risk, Backtesting experts)"
echo "- Communication style guidelines" 
echo "- Jesse framework documentation (utils, debugging, etc.)"
echo "- Strategy properties and methods"
echo "- Complete example strategies (8 full examples)"
echo ""
echo "🔧 Usage: Replace original jessegpt.md with jessegpt_modular.md"
echo "🧰 Fabric patterns can now be used to extract specific expertise on demand"