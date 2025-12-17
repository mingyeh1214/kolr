import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    // 讀取 CSV 檔案
    const csvPath = path.join(process.cwd(), 'public', 'iglink.csv');
    
    if (!fs.existsSync(csvPath)) {
      return NextResponse.json(
        { error: '找不到 CSV 檔案' },
        { status: 404 }
      );
    }
    
    const csvContent = fs.readFileSync(csvPath, 'utf-8');
    
    // 解析 CSV
    const lines = csvContent.split('\n').filter(line => line.trim());
    
    if (lines.length === 0) {
      return NextResponse.json(
        { error: 'CSV 檔案為空' },
        { status: 400 }
      );
    }
    
    // 跳過標題行，計算 image_done 為 true 的筆數
    let completedCount = 0;
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // 處理 CSV：分割第一個逗號
      const firstCommaIndex = line.indexOf(',');
      if (firstCommaIndex !== -1) {
        const image_done = line.substring(firstCommaIndex + 1).trim().toLowerCase();
        if (image_done === 'true') {
          completedCount++;
        }
      }
    }
    
    return NextResponse.json({
      completedCount,
      total: lines.length - 1 // 減去標題行
    });
  } catch (error) {
    console.error('讀取 CSV 錯誤:', error);
    const errorMessage = error instanceof Error ? error.message : '未知錯誤';
    return NextResponse.json(
      { error: `讀取 CSV 檔案時發生錯誤: ${errorMessage}` },
      { status: 500 }
    );
  }
}

