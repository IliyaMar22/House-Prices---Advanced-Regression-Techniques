#!/bin/bash
# Quick Test Script for Financial Review Pipeline

echo "======================================================================"
echo "Financial Review Pipeline - Quick Test"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 available${NC}"
echo ""

# Step 2: Create virtual environment
echo "Step 2: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}→ Virtual environment already exists${NC}"
fi
echo ""

# Step 3: Activate and install dependencies
echo "Step 3: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Step 4: Verify sample data
echo "Step 4: Verifying sample data..."
if [ -f "data/mapping.csv" ] && [ -f "data/sample_fagl03.csv" ]; then
    MAPPING_LINES=$(wc -l < data/mapping.csv)
    FAGL_LINES=$(wc -l < data/sample_fagl03.csv)
    echo -e "${GREEN}✓ Mapping file: $MAPPING_LINES lines${NC}"
    echo -e "${GREEN}✓ FAGL03 file: $FAGL_LINES lines${NC}"
else
    echo -e "${RED}✗ Sample data files not found${NC}"
    exit 1
fi
echo ""

# Step 5: Run dry-run
echo "Step 5: Running validation (dry-run)..."
python -m fin_review.cli \
    --mapping data/mapping.csv \
    --fagl-file data/sample_fagl03.csv \
    --out-dir reports/ \
    --dry-run
    
DRY_RUN_EXIT=$?
echo ""

if [ $DRY_RUN_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Validation passed!${NC}"
    echo ""
    
    # Step 6: Run full pipeline
    echo "Step 6: Running full analysis..."
    python -m fin_review.cli \
        --mapping data/mapping.csv \
        --fagl-file data/sample_fagl03.csv \
        --out-dir reports/
    
    FULL_RUN_EXIT=$?
    echo ""
    
    if [ $FULL_RUN_EXIT -eq 0 ]; then
        echo -e "${GREEN}======================================================================"
        echo -e "✓ SUCCESS! Pipeline completed successfully"
        echo -e "======================================================================${NC}"
        echo ""
        echo "Generated reports in: reports/"
        echo ""
        echo "Next steps:"
        echo "  1. Open Excel: open reports/*/summary.xlsx"
        echo "  2. Open PowerPoint: open reports/*/executive_deck.pptx"
        echo "  3. Launch dashboard: streamlit run fin_review/dashboard/app.py"
    else
        echo -e "${RED}✗ Full pipeline failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Validation failed${NC}"
    exit 1
fi

