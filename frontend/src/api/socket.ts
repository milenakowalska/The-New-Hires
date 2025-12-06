import { io } from "socket.io-client";

const socket = io(import.meta.env.VITE_BASE_API_URL, {
    transports: ['websocket'],
    autoConnect: true,
    withCredentials: true
});

export default socket;
