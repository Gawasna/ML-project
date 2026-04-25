import { GoogleGenAI, Type } from "@google/genai";
import { DatasetItem, ModelConfig } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

export async function generateDatasetBatch(
  chunks: string[],
  topicName: string,
  styleName: string,
  contextDescription: string,
  modelConfig: ModelConfig,
  isReverseMode: boolean = false
): Promise<Omit<DatasetItem, "id">[]> {
  const prompt = isReverseMode ? `
Bạn là một chuyên gia chuẩn bị dữ liệu (Data Engineer) cho việc huấn luyện mô hình ngôn ngữ lớn (Instruction Tuning).
Nhiệm vụ: Xử lý danh sách các đoạn văn bản đầu vào (tiếng Việt) để tạo ra các cặp dữ liệu huấn luyện chất lượng cao gồm 'instruction', 'input' (tiếng Anh), và 'output' (tiếng Việt đã làm sạch).
Mục tiêu cuối cùng vẫn là tạo tập dữ liệu dịch từ Tiếng Anh sang Tiếng Việt.

QUAN TRỌNG: Bạn PHẢI xử lý TOÀN BỘ nội dung của dữ liệu đầu vào, không được bỏ sót bất kỳ đoạn nào.

Cấu hình:
- Chủ đề (Topic) bắt buộc: ${topicName}
${styleName ? `- Phong cách (Style) tùy chọn: ${styleName}` : ''}
${contextDescription ? `- Bối cảnh (Context) tùy chọn: ${contextDescription}` : ''}

Quy trình xử lý:
1. LÀM SẠCH VÀ CHUẨN HÓA DỮ LIỆU TIẾNG VIỆT:
   - Dữ liệu đầu vào là các câu hoặc đoạn văn ngắn tiếng Việt.
   - BẠN PHẢI giữ nguyên cấu trúc câu. KHÔNG ĐƯỢC gộp nhiều đoạn lại với nhau.
   - Làm sạch dữ liệu: Loại bỏ ký tự rác, từ lặp thừa, và sửa lỗi chính tả nếu có.
   - Kết quả làm sạch này sẽ là trường 'output' (đích đến của mô hình dịch).

2. DỊCH THUẬT SANG TIẾNG ANH (TẠO INPUT):
   - Dịch đoạn tiếng Việt (đã làm sạch) sang tiếng Anh.
   - Đảm bảo văn phong tự nhiên, đúng ngữ cảnh.
   - Kết quả dịch thuật tiếng Anh này sẽ là trường 'input' (đầu vào của mô hình dịch).

Dữ liệu đầu vào (JSON array các chuỗi tiếng Việt):
${JSON.stringify(chunks)}

Hãy trả về mảng JSON chứa các đối tượng có cấu trúc: { "input": string, "output": string }.
Trong đó 'input' là tiếng Anh, 'output' là tiếng Việt.
Lưu ý: Số lượng phần tử trả về có thể nhiều hơn số lượng đầu vào nếu bạn thực hiện chia nhỏ dữ liệu.
  ` : `
Bạn là một chuyên gia chuẩn bị dữ liệu (Data Engineer) cho việc huấn luyện mô hình ngôn ngữ lớn (Instruction Tuning).
Nhiệm vụ: Xử lý danh sách các đoạn văn bản đầu vào để tạo ra các cặp dữ liệu huấn luyện chất lượng cao gồm 'instruction', 'input' (đã làm sạch), và 'output'.

QUAN TRỌNG: Bạn PHẢI xử lý TOÀN BỘ nội dung của dữ liệu đầu vào, không được bỏ sót bất kỳ đoạn nào.

Cấu hình:
- Chủ đề (Topic) bắt buộc: ${topicName}
${styleName ? `- Phong cách (Style) tùy chọn: ${styleName}` : ''}
${contextDescription ? `- Bối cảnh (Context) tùy chọn: ${contextDescription}` : ''}

Quy trình xử lý:
1. LÀM SẠCH VÀ CHUẨN HÓA DỮ LIỆU (Data Cleaning & Normalization):
   - Dữ liệu đầu vào ('input') là các câu hoặc đoạn văn ngắn đã được tiền xử lý.
   - BẠN PHẢI giữ nguyên cấu trúc câu của 'input' này. KHÔNG ĐƯỢC gộp nhiều 'input' lại với nhau.
   - Làm sạch dữ liệu: Loại bỏ ký tự rác (VD: >>, --, ...), từ lặp thừa, âm thanh trong ngoặc (VD: [panting], *sigh*), và sửa lỗi chính tả nếu có.
   - Mỗi chuỗi trong mảng đầu vào sẽ tương ứng với một đối tượng trong mảng kết quả trả về.

2. DỊCH THUẬT / TẠO OUTPUT:
   - Dịch thuật 'input' (đã được làm sạch ở bước 1) sang tiếng Việt.
   - Đảm bảo văn phong tự nhiên, đúng ngữ cảnh và tuân thủ cấu hình chủ đề/phong cách/bối cảnh.
   - Kết quả dịch thuật sẽ là trường 'output'.

Dữ liệu đầu vào (JSON array các chuỗi):
${JSON.stringify(chunks)}

Hãy trả về mảng JSON chứa các đối tượng có cấu trúc: { "input": string, "output": string }.
Lưu ý: Số lượng phần tử trả về có thể nhiều hơn số lượng đầu vào nếu bạn thực hiện chia nhỏ dữ liệu.
  `;

  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            input: { type: Type.STRING },
            output: { type: Type.STRING }
          },
          required: ["input", "output"]
        }
      },
      temperature: modelConfig.temperature,
      topP: modelConfig.topP,
      topK: modelConfig.topK,
    }
  });

  const text = response.text;
  if (!text) throw new Error("Không nhận được phản hồi từ API.");
  const parsed = JSON.parse(text);
  return parsed.map((item: any) => ({
    instruction: `Dịch thuật sang Tiếng việt theo chủ đề ${topicName}`,
    input: item.input,
    output: item.output
  }));
}

export async function processAllChunks(
  chunks: string[],
  topicName: string,
  styleName: string,
  contextDescription: string,
  modelConfig: ModelConfig,
  isReverseMode: boolean,
  onProgress: (progress: number, newItems: DatasetItem[]) => void,
  signal?: AbortSignal
) {
  const BATCH_SIZE = 3; // Giảm batch size xuống để đảm bảo AI xử lý hết dữ liệu
  const totalBatches = Math.ceil(chunks.length / BATCH_SIZE);
  
  for (let i = 0; i < totalBatches; i++) {
    if (signal?.aborted) {
      throw new Error("Đã dừng xử lý.");
    }
    const batch = chunks.slice(i * BATCH_SIZE, (i + 1) * BATCH_SIZE);
    try {
      const results = await generateDatasetBatch(batch, topicName, styleName, contextDescription, modelConfig, isReverseMode);
      const itemsWithIds = results.map(r => ({
        ...r,
        id: crypto.randomUUID()
      }));
      onProgress((i + 1) / totalBatches, itemsWithIds);
    } catch (error) {
      console.error(`Lỗi xử lý batch ${i}:`, error);
      throw new Error(`Lỗi xử lý dữ liệu ở tiến trình ${i + 1}/${totalBatches}`);
    }
  }
}
