import React from 'react';
import { DatasetItem } from '../types';
import { Trash2, Database } from 'lucide-react';

interface Props {
  items: DatasetItem[];
  onUpdateItem: (id: string, field: keyof DatasetItem, value: string) => void;
  onDeleteItem: (id: string) => void;
}

export function DataReviewZone({ items, onUpdateItem, onDeleteItem }: Props) {
  if (items.length === 0) {
    return (
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 flex flex-col items-center justify-center text-center gap-3">
        <Database className="w-10 h-10 text-zinc-700" />
        <p className="text-zinc-500 text-sm">Chưa có dữ liệu. Vui lòng cấu hình và tạo tập dữ liệu.</p>
      </section>
    );
  }

  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-900/50">
        <h2 className="text-sm font-medium text-zinc-100">Kiểm duyệt dữ liệu</h2>
        <span className="text-xs text-zinc-500 font-mono">Tổng số: {items.length} bản ghi</span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="bg-zinc-950/50 border-b border-zinc-800 text-zinc-400 text-xs uppercase tracking-wider">
              <th className="px-4 py-3 font-medium w-16 text-center">ID</th>
              <th className="px-4 py-3 font-medium w-1/4">Instruction (Có thể chỉnh sửa)</th>
              <th className="px-4 py-3 font-medium w-1/4">Input (Có thể chỉnh sửa)</th>
              <th className="px-4 py-3 font-medium w-1/4">Output (Có thể chỉnh sửa)</th>
              <th className="px-4 py-3 font-medium w-16 text-center">Hành động</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {items.map((item, index) => (
              <tr key={item.id} className="hover:bg-zinc-800/20 transition-colors group">
                <td className="px-4 py-3 text-zinc-600 font-mono text-xs text-center align-top">
                  <div className="flex flex-col items-center gap-1.5">
                    <span>{index + 1}</span>
                    {item.isEval ? (
                      <span className="bg-indigo-500/20 text-indigo-400 px-1.5 py-0.5 rounded text-[10px] font-medium tracking-wider">EVAL</span>
                    ) : (
                      <span className="bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded text-[10px] font-medium tracking-wider">TRAIN</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 align-top">
                  <textarea
                    value={item.instruction}
                    onChange={(e) => onUpdateItem(item.id, 'instruction', e.target.value)}
                    className="w-full bg-transparent border border-transparent hover:border-zinc-700 focus:border-zinc-600 focus:bg-zinc-950 rounded p-1.5 text-zinc-300 resize-y min-h-[80px] text-sm focus:outline-none transition-all"
                  />
                </td>
                <td className="px-4 py-3 align-top">
                  <textarea
                    value={item.input}
                    onChange={(e) => onUpdateItem(item.id, 'input', e.target.value)}
                    className="w-full bg-transparent border border-transparent hover:border-zinc-700 focus:border-zinc-600 focus:bg-zinc-950 rounded p-1.5 text-zinc-300 resize-y min-h-[80px] text-sm focus:outline-none transition-all"
                  />
                </td>
                <td className="px-4 py-3 align-top">
                  <textarea
                    value={item.output}
                    onChange={(e) => onUpdateItem(item.id, 'output', e.target.value)}
                    className="w-full bg-transparent border border-transparent hover:border-zinc-700 focus:border-zinc-600 focus:bg-zinc-950 rounded p-1.5 text-zinc-300 resize-y min-h-[80px] text-sm focus:outline-none transition-all"
                  />
                </td>
                <td className="px-4 py-3 align-top text-center">
                  <button
                    onClick={() => onDeleteItem(item.id)}
                    className="p-2 text-zinc-600 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                    title="Xóa dòng"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
