import axios from 'axios';
import { config } from '../../config/env';
import { chatHistory, scanHistory } from '../../data/mockData';

/**
 * Dedicated Axios instance for Agentic AI Engine.
 * Points to the FastAPI server running on port 8000 by default.
 */
const aiApiClient = axios.create({
  baseURL: config.ai.baseUrl,
  timeout: 60000, // AI processing can take up to a minute
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor to inject Token (same token from .NET backend if shared secret is used)
aiApiClient.interceptors.request.use(
  (reqConfig) => {
    const token = localStorage.getItem('medagent_token');
    if (token) {
      reqConfig.headers.Authorization = `Bearer ${token}`;
    }
    return reqConfig;
  },
  (error) => Promise.reject(error)
);

export const AIService = {
  /**
   * Main consultation endpoint utilizing the LangGraph pipeline.
   */
  consult: async (patientId, text) => {
    try {
      const payload = {
        patient_id: patientId || "GUEST",
        symptoms: text,
        request_second_opinion: false,
        interaction_mode: "patient"
      };
      
      const response = await aiApiClient.post('/clinical/consult', payload);
      const data = response.data;
      
      return {
        id: Date.now() + 1,
        sender: 'ai',
        text: data.final_response || "I couldn't generate a complete response.",
        time: 'Just now',
        tags: [data.risk_level ? `Risk: ${data.risk_level}` : 'AI Generated']
      };
    } catch (error) {
      console.warn("AI Engine unreachable, falling back to basic mock response.", error);
      // Fallback for demo purposes if backend isn't fully running
      return {
        id: Date.now() + 1,
        sender: 'ai',
        text: "I am unable to connect to the medical AI engine right now. Please ensure the Python backend is running on port 8000.",
        time: 'Just now',
        tags: ['Offline Mode']
      };
    }
  },

  getChatHistory: async (patientId) => {
    try {
      const response = await aiApiClient.get('/data/history');
      // Format backend response into chat UI components here
      // For now, if no history returned or if format varies, fallback to mock
      if (response.data && response.data.length > 0) {
        return response.data;
      }
      return chatHistory.slice(0, 5); 
    } catch (error) {
      console.warn("Failed to fetch chat history, returning mock", error);
      return chatHistory.slice(0, 5); // From mockData
    }
  },

  getDiagnosisHistory: async () => {
    try {
      const response = await aiApiClient.get('/patient/history');
      return response.data;
    } catch (error) {
      // Fallback to static mock
      return [
        { id: 'd1', title: 'Acute Gastritis', date: 'Oct 05, 2023', folder: 'General', confidence: 92 },
        { id: 'd2', title: 'Atrial Fibrillation', date: 'Sep 28, 2023', folder: 'Cardiology', confidence: 98 },
        { id: 'd3', title: 'Migraine Tracking', date: 'Sep 12, 2023', folder: 'Neurology', confidence: 85 },
        { id: 'd4', title: 'Post-Op Follow-up', date: 'Aug 30, 2023', folder: 'Cardiology', confidence: 95 }
      ];
    }
  },

  getDoctors: async () => {
    // Return verified doctors static catalog as no .NET table exists yet
    return [
      { id: 1, name: 'Dr. Sarah Jenkins', specialty: 'Cardiology', rating: 4.9, experience: '15 years', status: 'ONLINE', waitTime: '5 mins', distance: '2.4 km' },
      { id: 2, name: 'Dr. Michael Chen', specialty: 'Neurology', rating: 4.8, experience: '12 years', status: 'ONLINE', waitTime: '10 mins', distance: '3.1 km' },
      { id: 3, name: 'Dr. Emily Rodriguez', specialty: 'General Physician', rating: 4.9, experience: '8 years', status: 'ONLINE', waitTime: '0 mins', distance: '1.2 km' },
      { id: 4, name: 'Dr. James Wilson', specialty: 'Orthopedics', rating: 4.7, experience: '20 years', status: 'OFFLINE', waitTime: '-', distance: '5.5 km' },
      { id: 5, name: 'Dr. Anita Patel', specialty: 'Pediatrics', rating: 4.9, experience: '10 years', status: 'ONLINE', waitTime: '15 mins', distance: '4.0 km' },
      { id: 6, name: 'Dr. Robert Taylor', specialty: 'General Physician', rating: 4.6, experience: '25 years', status: 'OFFLINE', waitTime: '-', distance: '8.2 km' },
    ];
  },

  getEmergencyFacilities: async () => {
    return [
      { id: 1, name: "City General Hospital", type: "hospital", distance: "2.4 km", arrivalMinutes: 8, location: { lat: 0, lng: 0 }, details: "Level 1 Trauma Center, 24/7 ER", phone: "+1-555-0199" },
      { id: 2, name: "St. Jude's Medical Center", type: "hospital", distance: "5.1 km", arrivalMinutes: 14, location: { lat: 0, lng: 0 }, details: "Specialized Cardiac Care, 24/7 ER", phone: "+1-555-0200" },
      { id: 3, name: "Paramedic Unit Alpha", type: "ambulance", distance: "Unknown", arrivalMinutes: null, location: { lat: 0, lng: 0 }, details: "Advanced Life Support Unit", phone: "+1-555-0911" }
    ];
  }
};
