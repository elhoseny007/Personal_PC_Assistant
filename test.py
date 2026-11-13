from history import (
    save_chat_message,
    load_chat_history,
    clear_chat_history,
)

# Save messages in two separate chats
save_chat_message("chat_A", "user", "Hello")
save_chat_message("chat_A", "assistant", "Hi!")

save_chat_message("chat_B", "user", "Upload my file")
save_chat_message("chat_B", "assistant", "Which file?")

# Load each chat
print("CHAT A:")
print(load_chat_history("chat_A"))

print("CHAT B:")
print(load_chat_history("chat_B"))
