'use client';

import { ChevronLeft, X, Bookmark, ChevronRight } from 'lucide-react';

interface ControlBarProps {
  onPrevious: () => void;
  onReject: () => void;
  onBookmark: () => void;
  onNext: () => void;
  disabled?: {
    previous?: boolean;
    next?: boolean;
  };
  loading?: boolean;
}

export default function ControlBar({
  onPrevious,
  onReject,
  onBookmark,
  onNext,
  disabled = {},
  loading = false
}: ControlBarProps) {
  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
      <div className="bg-black/80 backdrop-blur-xl rounded-full px-4 py-3 shadow-lg border border-white/10">
        <div className="flex items-center gap-3">
          {/* 上一個按鈕 */}
          <button
            onClick={onPrevious}
            disabled={disabled.previous || loading}
            className="p-2 rounded-full hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="上一個"
          >
            <ChevronLeft className="w-5 h-5 text-white" />
          </button>
          
          {/* X 放棄按鈕 */}
          <button
            onClick={onReject}
            disabled={loading}
            className="p-2 rounded-full hover:bg-red-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="放棄"
          >
            <X className="w-5 h-5 text-red-400" />
          </button>
          
          {/* Bookmark 按鈕 */}
          <button
            onClick={onBookmark}
            disabled={loading}
            className="p-2 rounded-full hover:bg-yellow-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="標記"
          >
            <Bookmark className="w-5 h-5 text-yellow-400" />
          </button>
          
          {/* 下一個按鈕 */}
          <button
            onClick={onNext}
            disabled={disabled.next || loading}
            className="p-2 rounded-full hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="下一個"
          >
            <ChevronRight className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

