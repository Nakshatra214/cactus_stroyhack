import { useEffect, useState } from "react";
import { Scene } from "@/lib/store";

export default function useSceneEditor() {
    const [socket, setSocket] = useState<WebSocket | null>(null);
    const [updatedScene, setUpdatedScene] = useState<Scene | null>(null);
    const [statusMessage, setStatusMessage] = useState<string>("");

    useEffect(() => {
        // Determine WebSocket URL based on environment
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = process.env.NEXT_PUBLIC_API_URL
            ? process.env.NEXT_PUBLIC_API_URL.replace(/^http(s?):\/\//, `${protocol}//`)
            : "ws://localhost:8000";

        const ws = new WebSocket(`${host}/ws/edit-scene`);

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === "scene_updated") {
                    setUpdatedScene(data.scene);
                    setStatusMessage(""); // Clear status on completion
                } else if (data.type === "status") {
                    setStatusMessage(data.message);
                }
            } catch (e) {
                console.error("WebSocket message parsing error", e);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
        };

        setSocket(ws);

        return () => {
            ws.close();
        };
    }, []);

    const editSceneSocket = (scene: Scene, instruction: string) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            // Set an initial status immediately for better UX
            setStatusMessage("Sending instructions to AI...");
            setUpdatedScene(null);
            socket.send(
                JSON.stringify({
                    type: "edit_scene",
                    scene,
                    instruction,
                })
            );
        } else {
            console.error("WebSocket is not connected");
        }
    };

    return { editSceneSocket, updatedScene, statusMessage };
}
