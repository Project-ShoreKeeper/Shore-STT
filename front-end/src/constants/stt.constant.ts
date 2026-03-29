/**
 * Cấu hình cho module STT
 */

// WebSocket URL kết nối tới Backend STT Server
// Trong production, thay bằng env variable hoặc reverse proxy
export const STT_WS_URL = "ws://localhost:8000/ws/audio";

// Ngôn ngữ mặc định cho STT
export const STT_DEFAULT_LANGUAGE = "en";

// Danh sách ngôn ngữ hỗ trợ
export const STT_LANGUAGES = [
  { value: "en", label: "English" },
  { value: "vi", label: "Tiếng Việt" },
  { value: "auto", label: "Auto Detect" },
] as const;
