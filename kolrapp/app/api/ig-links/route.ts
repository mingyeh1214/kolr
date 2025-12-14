import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

interface CSVRow {
  link: string;
  image_done: string;
  index: number;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const currentIndex = searchParams.get('index');
    
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
    
    const headers = lines[0].split(',').map(h => h.trim());
    
    if (headers[0] !== 'link' || headers[1] !== 'image_done') {
      return NextResponse.json(
        { error: `CSV 格式不正確，預期標題為 "link,image_done"，實際為 "${lines[0]}"` },
        { status: 400 }
      );
    }
    
    // 解析所有行
    const rows: CSVRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      // 處理 CSV：分割第一個逗號
      const firstCommaIndex = line.indexOf(',');
      if (firstCommaIndex === -1) {
        // 沒有逗號，只有 link
        rows.push({ link: line, image_done: '', index: i - 1 });
      } else {
        const link = line.substring(0, firstCommaIndex).trim();
        const image_done = line.substring(firstCommaIndex + 1).trim();
        rows.push({ link, image_done, index: i - 1 });
      }
    }
    
    // 找到所有未完成的項目（image_done 為空）
    const pendingRows = rows.filter(row => !row.image_done || row.image_done === '');
    const pendingUrls = pendingRows.map(row => row.link);
    
    if (pendingRows.length === 0) {
      return NextResponse.json({
        currentIndex: -1,
        currentUrl: null,
        total: 0,
        urls: [],
        pendingIndices: [],
        currentPosition: 0,
        message: '沒有未完成的項目'
      });
    }
    
    // 如果提供了索引，使用該索引；否則使用第一個未完成項目的索引
    let targetIndex = 0;
    if (currentIndex !== null) {
      const index = parseInt(currentIndex, 10);
      const foundIndex = pendingRows.findIndex(row => row.index === index);
      if (foundIndex !== -1) {
        targetIndex = foundIndex;
      }
    }
    
    const currentRow = pendingRows[targetIndex];
    
    // 返回所有未完成項目的索引列表，方便導航
    const pendingIndices = pendingRows.map(row => row.index);
    
    return NextResponse.json({
      currentIndex: currentRow.index,
      currentUrl: currentRow.link,
      total: pendingRows.length,
      urls: pendingUrls,
      pendingIndices: pendingIndices,
      currentPosition: targetIndex + 1
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

