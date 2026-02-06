import { GoogleGenAI, Type } from "@google/genai";
import { Team, Risk, Dependency, Feature } from '../types';

const getAiClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    console.error("API_KEY is missing");
    return null;
  }
  return new GoogleGenAI({ apiKey });
};

export const analyzePlan = async (
  teams: Team[],
  currentRisks: Risk[],
  dependencies: Dependency[]
): Promise<{ risks: any[], summary: string, suggestions: string[] }> => {
  const ai = getAiClient();
  if (!ai) return { risks: [], summary: "API Key missing", suggestions: [] };

  const context = {
    teams: teams.map(t => ({
      name: t.name,
      capacity: t.capacity,
      load: t.features.reduce((acc, f) => acc + f.points, 0),
      features: t.features.map(f => ({ title: f.title, points: f.points }))
    })),
    dependencies: dependencies.length,
    knownRisks: currentRisks.map(r => r.description)
  };

  const prompt = `Analyze this PI Planning data. Identify 3 potential new risks based on load/capacity and feature complexity. 
  Provide a brief executive summary of the plan's health. 
  Provide 2 actionable suggestions for improvement.
  
  Data: ${JSON.stringify(context)}`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            risks: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  description: { type: Type.STRING },
                  impact: { type: Type.STRING, enum: ['High', 'Medium', 'Low'] }
                }
              }
            },
            summary: { type: Type.STRING },
            suggestions: {
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          }
        }
      }
    });

    const text = response.text;
    if (!text) return { risks: [], summary: "No response generated", suggestions: [] };
    return JSON.parse(text);
  } catch (error) {
    console.error("Gemini analysis failed", error);
    return { risks: [], summary: "Analysis failed due to error.", suggestions: [] };
  }
};

export const suggestObjectives = async (teams: Team[]): Promise<string[]> => {
  const ai = getAiClient();
  if (!ai) return ["API Key missing"];

  const teamData = teams.map(t => ({
    name: t.name,
    features: t.features.map(f => f.title)
  }));

  const prompt = `Based on these features assigned to teams, suggest 3 high-level PI Objectives that summarize the business value being delivered. Data: ${JSON.stringify(teamData)}`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            objectives: {
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          }
        }
      }
    });
    
    const text = response.text;
    if (!text) return [];
    const json = JSON.parse(text);
    return json.objectives || [];
  } catch (error) {
    console.error("Objectives generation failed", error);
    return [];
  }
};
