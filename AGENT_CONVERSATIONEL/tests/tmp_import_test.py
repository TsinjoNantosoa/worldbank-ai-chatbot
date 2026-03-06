import sys
sys.path.append(r"c:\Users\Tsinjo\Documents\H4H\H4H_AAA_DATA_chatbot_careers\WORLD BANK")
try:
    import core.embeddings_loader as el
    print('IMPORT_OK')
except Exception as e:
    print('IMPORT_FAIL', type(e).__name__, str(e))
