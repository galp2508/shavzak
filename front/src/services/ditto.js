import { init, Ditto } from "@dittolive/ditto";

let ditto = null;

export const initDitto = async () => {
  if (ditto) return ditto;

  try {
    await init();
    
    ditto = new Ditto({
      type: "online",
      appID: import.meta.env.VITE_DITTO_APP_ID,
      token: import.meta.env.VITE_DITTO_TOKEN,
    });

    await ditto.start();
    console.log("✅ Ditto started successfully");
    return ditto;
  } catch (error) {
    console.error("🔴 Failed to start Ditto:", error);
    throw error;
  }
};

export const getDitto = () => ditto;
