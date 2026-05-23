name: Global Daily Intelligence

on:
  schedule:
    - cron: '0 */2 * * *'
  workflow_dispatch:

jobs:
  collect:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # 获取完整历史以便 rebase
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Dependencies
        run: |
          pip install requests beautifulsoup4

      - name: Run Global Collection
        env:
          ZHIPU_API_KEY: ${{ secrets.ZHIPU_API_KEY }}
        run: python src/scripts/collect_all.py

      - name: Sync and Deploy Data
        run: |
          git config --local user.email "bot@intel-daily.com"
          git config --local user.name "Intelligence Bot"
          git add src/data/rewrite/
          # 先拉取远程修改，防止冲突
          git pull --rebase origin main
          git commit -m "update: dual-language data $(date)" || exit 0
          git push origin main
