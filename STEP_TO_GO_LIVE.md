1. (First Time) Create 2 shortcuts of OBS on your desktop. Rename them to Ground 1 and Ground 2.
   *(Note: If Ground 2 is a portable version, create the shortcut directly from the portable folder's obs64.exe)*
2. (First Time) Right-click each shortcut, hit Properties, and append the following to the Target field:
    - Ground 1 (Standard): ` --multi --websocket_port 4566 --websocket_password Admin6011`
    - Ground 2 (Portable): ` --portable --websocket_port 4555 --websocket_password Admin6011`
3. **(Crucial Step for Portable OBS)** Open your Ground 2 (Portable) OBS instance:
    - Go to **Tools -> WebSocket Server Settings**.
    - Check **"Enable WebSocket server"** (it is disabled by default in portable mode).
    - Click **Apply** and **OK**, then close OBS.
4. Run both of these OBS instances using your newly updated shortcuts.
5. Run the Automation App (`python app.py`).
6. Insert match_id, fetch title, select your ground, and click Go Live.