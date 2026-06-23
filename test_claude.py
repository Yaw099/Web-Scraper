from claude_analysis import analyze_text_file

result = analyze_text_file(
    "output/www.adminmonitor.com_tx_puct_open_meeting_20260326.txt",
    "analysis"
)

print("Analysis saved to:")
print(result)