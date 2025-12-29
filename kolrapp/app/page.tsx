'use client';

import { useState, useEffect } from 'react';
import ControlBar from './components/ControlBar';

interface IGLinkData {
  currentIndex: number;
  currentUrl: string | null;
  total: number;
  urls: string[];
  pendingIndices: number[];
  currentPosition?: number;
}

type ViewMode = 'iframe' | 'newtab' | 'viewer';
type SearchDirection = 'forward' | 'reverse';

export default function Home() {
  const [data, setData] = useState<IGLinkData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPosition, setCurrentPosition] = useState(0);
  const [viewMode, setViewMode] = useState<ViewMode>('newtab');
  const [completedCount, setCompletedCount] = useState<number | null>(null);
  const [searchDirection, setSearchDirection] = useState<SearchDirection>('forward');

  // 載入當前項目
  const loadCurrentItem = async (index?: number, direction?: SearchDirection) => {
    setLoading(true);
    setError(null);
    
    try {
      const dir = direction || searchDirection;
      let url = '/api/ig-links';
      
      if (index !== undefined) {
        url = `/api/ig-links?index=${index}`;
      } else {
        // 如果沒有指定索引，先獲取所有未完成項目的列表
        const listResponse = await fetch('/api/ig-links');
        if (listResponse.ok) {
          const listResult = await listResponse.json();
          if (listResult.pendingIndices && listResult.pendingIndices.length > 0) {
            // 正向：第一個，反向：最後一個
            const targetIndex = dir === 'forward' 
              ? listResult.pendingIndices[0]
              : listResult.pendingIndices[listResult.pendingIndices.length - 1];
            url = `/api/ig-links?index=${targetIndex}`;
          } else {
            // 沒有未完成的項目
            setData({
              currentIndex: -1,
              currentUrl: null,
              total: 0,
              urls: [],
              pendingIndices: [],
              currentPosition: 0
            });
            setCurrentPosition(0);
            setLoading(false);
            return;
          }
        }
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: '無法載入資料' }));
        throw new Error(errorData.error || `HTTP ${response.status}: 無法載入資料`);
      }
      
      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }
      
      if (!result.currentUrl && result.message) {
        // 沒有未完成的項目，這是正常情況，不是錯誤
        setData(result);
        setCurrentPosition(0);
        setLoading(false);
        return;
      }
      
      setData(result);
      // 根據方向調整位置顯示
      // API 返回的 currentPosition 是正向位置（1-based）
      if (dir === 'reverse') {
        // 反向時，位置是從後往前計算：total - currentPosition + 1
        setCurrentPosition(result.total - (result.currentPosition || 0) + 1);
      } else {
        setCurrentPosition(result.currentPosition || 0);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '發生未知錯誤');
      console.error('載入錯誤:', err);
    } finally {
      setLoading(false);
    }
  };

  // 載入已完成項目數量
  const loadCompletedCount = async () => {
    try {
      const response = await fetch('/api/completed-count');
      if (response.ok) {
        const result = await response.json();
        setCompletedCount(result.completedCount);
      }
    } catch (err) {
      console.error('載入已完成數量錯誤:', err);
    }
  };

  // 初始載入
  useEffect(() => {
    loadCurrentItem();
    loadCompletedCount();
  }, []);

  // 當 viewMode 為 newtab 且有 URL 時，自動在新分頁開啟
  useEffect(() => {
    if (viewMode === 'newtab' && data?.currentUrl && !loading) {
      window.open(data.currentUrl, '_blank');
    }
  }, [data?.currentUrl, viewMode, loading]);

  // 處理上一個
  const handlePrevious = async () => {
    if (!data) return;
    
    // 找到當前在 pendingIndices 中的位置
    const currentPendingIndex = data.pendingIndices.indexOf(data.currentIndex);
    
    if (searchDirection === 'forward') {
      // 正向：上一個是索引減 1
      if (currentPendingIndex > 0) {
        const prevIndex = data.pendingIndices[currentPendingIndex - 1];
        await loadCurrentItem(prevIndex, searchDirection);
      }
    } else {
      // 反向：上一個是索引加 1（因為是從後往前）
      if (currentPendingIndex < data.pendingIndices.length - 1) {
        const prevIndex = data.pendingIndices[currentPendingIndex + 1];
        await loadCurrentItem(prevIndex, searchDirection);
      }
    }
  };

  // 處理下一個
  const handleNext = async () => {
    if (!data) return;
    
    // 找到當前在 pendingIndices 中的位置
    const currentPendingIndex = data.pendingIndices.indexOf(data.currentIndex);
    
    if (searchDirection === 'forward') {
      // 正向：下一個是索引加 1
      if (currentPendingIndex < data.pendingIndices.length - 1) {
        const nextIndex = data.pendingIndices[currentPendingIndex + 1];
        await loadCurrentItem(nextIndex, searchDirection);
      }
    } else {
      // 反向：下一個是索引減 1（因為是從後往前）
      if (currentPendingIndex > 0) {
        const nextIndex = data.pendingIndices[currentPendingIndex - 1];
        await loadCurrentItem(nextIndex, searchDirection);
      }
    }
  };

  // 處理切換檢索方向
  const handleToggleDirection = async () => {
    const newDirection = searchDirection === 'forward' ? 'reverse' : 'forward';
    setSearchDirection(newDirection);
    
    // 切換方向時，載入新方向的起始項目（正向：第一個，反向：最後一個）
    await loadCurrentItem(undefined, newDirection);
  };

  // 處理放棄
  const handleReject = async () => {
    if (!data || !data.currentUrl) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/update-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: data.currentUrl,
          status: 'false'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // 更新已完成數量
        await loadCompletedCount();
        // 載入下一個項目
        if (result.nextIndex !== null) {
          await loadCurrentItem(result.nextIndex);
        } else if (result.remaining === 0) {
          // 沒有剩餘項目了
          setData({
            currentIndex: -1,
            currentUrl: null,
            total: 0,
            urls: [],
            pendingIndices: [],
            currentPosition: 0
          });
          setCurrentPosition(0);
        } else {
          // 重新載入第一個未完成的項目
          await loadCurrentItem();
        }
      } else {
        throw new Error(result.error || '更新失敗');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失敗');
    } finally {
      setLoading(false);
    }
  };

  // 處理標記
  const handleBookmark = async () => {
    if (!data || !data.currentUrl) return;
    
    setLoading(true);
    try {
      const response = await fetch('/api/update-status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: data.currentUrl,
          status: 'true'
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // 更新已完成數量
        await loadCompletedCount();
        // 載入下一個項目
        if (result.nextIndex !== null) {
          await loadCurrentItem(result.nextIndex);
        } else if (result.remaining === 0) {
          // 沒有剩餘項目了
          setData({
            currentIndex: -1,
            currentUrl: null,
            total: 0,
            urls: [],
            pendingIndices: [],
            currentPosition: 0
          });
          setCurrentPosition(0);
        } else {
          // 重新載入第一個未完成的項目
          await loadCurrentItem();
        }
      } else {
        throw new Error(result.error || '更新失敗');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden bg-black">
      {/* 頂部工具欄 */}
      <ControlBar
        onPrevious={handlePrevious}
        onReject={handleReject}
        onBookmark={handleBookmark}
        onNext={handleNext}
        onToggleDirection={handleToggleDirection}
        searchDirection={searchDirection}
        disabled={{
          previous: searchDirection === 'forward' 
            ? (!data || currentPosition <= 1)
            : (!data || currentPosition >= data.total),
          next: searchDirection === 'forward'
            ? (!data || currentPosition >= data.total)
            : (!data || currentPosition <= 1)
        }}
        loading={loading}
      />
      
      {/* 主內容區域 */}
      <div className="h-full w-full pt-20">
        {loading && !data && (
          <div className="flex items-center justify-center h-full">
            <div className="text-white text-lg">載入中...</div>
          </div>
        )}
        
        {error && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="text-red-400 text-lg">{error}</div>
            <button
              onClick={() => {
                setError(null);
                loadCurrentItem();
              }}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
            >
              重試
            </button>
            <div className="text-white/60 text-sm max-w-md text-center">
              如果問題持續，請檢查：
              <br />1. CSV 檔案是否存在於 public/iglink.csv
              <br />2. 開發伺服器是否正常運行
              <br />3. 瀏覽器控制台是否有詳細錯誤訊息
            </div>
          </div>
        )}
        
        {data && !data.currentUrl && (
          <div className="flex flex-col items-center justify-center h-full gap-4">
            <div className="text-white text-lg">沒有未完成的項目</div>
            {completedCount !== null && (
              <div className="bg-green-500/20 backdrop-blur-sm rounded-lg px-4 py-2 text-green-400 text-sm border border-green-500/30">
                已完成: {completedCount} 筆
              </div>
            )}
            <button
              onClick={() => loadCurrentItem()}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white transition-colors"
            >
              重新載入
            </button>
          </div>
        )}
        
        {data && data.currentUrl && (
          <>
            {/* 顯示當前位置資訊和查看模式選擇 */}
            <div className="absolute top-20 left-4 z-40 flex items-center gap-3">
              <div className="bg-black/60 backdrop-blur-sm rounded-lg px-3 py-1 text-white text-sm">
                {currentPosition} / {data.total}
              </div>
              {completedCount !== null && (
                <div className="bg-green-500/20 backdrop-blur-sm rounded-lg px-3 py-1 text-green-400 text-sm border border-green-500/30">
                  已完成: {completedCount}
                </div>
              )}
              
              {/* 查看模式選擇 */}
              <div className="bg-black/60 backdrop-blur-sm rounded-lg px-2 py-1 flex gap-1">
                <button
                  onClick={() => {
                    setViewMode('newtab');
                    window.open(data.currentUrl!, '_blank');
                  }}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    viewMode === 'newtab'
                      ? 'bg-white/20 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                  title="在新分頁開啟"
                >
                  新分頁
                </button>
                <button
                  onClick={() => {
                    // 從 Instagram URL 提取用戶名
                    const username = data.currentUrl!.match(/instagram\.com\/([^/?]+)/)?.[1];
                    if (username) {
                      const viewerUrl = `https://www.picuki.com/profile/${username}`;
                      setViewMode('viewer');
                      window.open(viewerUrl, '_blank');
                    }
                  }}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    viewMode === 'viewer'
                      ? 'bg-white/20 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                  title="使用第三方查看器"
                >
                  查看器
                </button>
                <button
                  onClick={() => setViewMode('iframe')}
                  className={`px-2 py-1 rounded text-xs transition-colors ${
                    viewMode === 'iframe'
                      ? 'bg-white/20 text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                  title="嘗試嵌入（可能無法顯示）"
                >
                  嵌入
                </button>
              </div>
              
              {/* 直接開啟連結按鈕 */}
              <button
                onClick={() => window.open(data.currentUrl!, '_blank')}
                className="bg-blue-500/80 hover:bg-blue-500 rounded-lg px-3 py-1 text-white text-sm transition-colors"
                title="在新分頁開啟 Instagram"
              >
                開啟 IG
              </button>
            </div>
            
            {/* 顯示當前 URL 資訊 */}
            <div className="absolute top-20 right-4 z-40 bg-black/60 backdrop-blur-sm rounded-lg px-3 py-2 text-white text-xs max-w-md break-all">
              <div className="font-semibold mb-1">當前 URL:</div>
              <div className="text-white/80">{data.currentUrl}</div>
            </div>
            
            {/* 根據查看模式顯示內容 */}
            {viewMode === 'iframe' ? (
              <iframe
                src={data.currentUrl}
                className="w-full h-full border-0"
                title="Instagram"
                allow="encrypted-media"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
                onError={() => {
                  setError('無法載入 Instagram 頁面（Instagram 可能不允許嵌入）');
                }}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full gap-6 text-white">
                <div className="text-xl font-semibold">準備就緒</div>
                <div className="text-sm text-white/60 text-center max-w-md">
                  {viewMode === 'newtab' 
                    ? 'Instagram 應該已經在新分頁開啟。瀏覽完畢後，使用頂部工具欄進行操作：'
                    : '使用第三方查看器查看 Instagram 內容。瀏覽完畢後，使用頂部工具欄進行操作：'}
                </div>
                <div className="bg-white/10 rounded-lg p-4 space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-yellow-400">★</span>
                    <span>Bookmark：標記為已完成，自動跳到下一個</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-red-400">✗</span>
                    <span>放棄：標記為 false，自動跳到下一個</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-white/60">← →</span>
                    <span>上一個/下一個：切換到其他未完成的項目</span>
                  </div>
                </div>
                <button
                  onClick={() => window.open(data.currentUrl!, '_blank')}
                  className="bg-blue-500 hover:bg-blue-600 rounded-lg px-6 py-3 text-white font-medium transition-colors"
                >
                  在新分頁開啟 Instagram
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
