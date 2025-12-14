import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { url, status } = body;
    
    if (!url || status === undefined) {
      return NextResponse.json(
        { error: '缺少必要參數：url 和 status' },
        { status: 400 }
      );
    }
    
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
    const lines = csvContent.split('\n');
    const headers = lines[0];
    
    // 更新對應行的 image_done 欄位
    let updated = false;
    const updatedLines = lines.map((line, index) => {
      if (index === 0) return line; // 跳過標題行
      
      const trimmedLine = line.trim();
      if (!trimmedLine) return line;
      
      // 處理 CSV：分割第一個逗號
      const firstCommaIndex = trimmedLine.indexOf(',');
      if (firstCommaIndex === -1) {
        // 沒有逗號，只有 link
        if (trimmedLine === url) {
          updated = true;
          return `${url},${status}`;
        }
        return line;
      } else {
        const link = trimmedLine.substring(0, firstCommaIndex).trim();
        const image_done = trimmedLine.substring(firstCommaIndex + 1).trim();
        
        if (link === url) {
          updated = true;
          return `${link},${status}`;
        }
      }
      return line;
    });
    
    if (!updated) {
      return NextResponse.json(
        { error: '找不到對應的 URL' },
        { status: 404 }
      );
    }
    
    // 寫回檔案
    fs.writeFileSync(csvPath, updatedLines.join('\n'), 'utf-8');
    
    // 找到下一個未完成的項目
    const pendingRows: { link: string; index: number }[] = [];
    updatedLines.forEach((line, index) => {
      if (index === 0) return; // 跳過標題行
      
      const trimmedLine = line.trim();
      if (!trimmedLine) return;
      
      const firstCommaIndex = trimmedLine.indexOf(',');
      if (firstCommaIndex === -1) {
        // 沒有逗號，只有 link（視為未完成）
        pendingRows.push({ link: trimmedLine, index: index - 1 });
      } else {
        const link = trimmedLine.substring(0, firstCommaIndex).trim();
        const image_done = trimmedLine.substring(firstCommaIndex + 1).trim();
        
        if (!image_done || image_done === '') {
          pendingRows.push({ link, index: index - 1 });
        }
      }
    });
    
    // 找到當前 URL 的索引，然後找下一個
    const currentRowIndex = updatedLines.findIndex((line, index) => {
      if (index === 0) return false;
      const match = line.match(/^(.+?),(.*)$/);
      return match && match[1].trim() === url;
    }) - 1;
    
    // 找到下一個未完成的項目（在當前項目之後）
    const nextPending = pendingRows.find(row => row.index > currentRowIndex);
    
    return NextResponse.json({
      success: true,
      nextIndex: nextPending ? nextPending.index : null,
      nextUrl: nextPending ? nextPending.link : null,
      remaining: pendingRows.length
    });
  } catch (error) {
    console.error('更新 CSV 錯誤:', error);
    return NextResponse.json(
      { error: '更新 CSV 檔案時發生錯誤' },
      { status: 500 }
    );
  }
}

