export interface DatasetItem {
  id: string;
  instruction: string;
  input: string;
  output: string;
  isEval?: boolean;
}

export interface ModelConfig {
  temperature: number;
  topP: number;
  topK: number;
}
