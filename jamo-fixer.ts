import type { Tool } from "./types";

export const jamoFixer: Tool = {
  slug: "jamo-fixer",
  name: "Jamo Fixer",
  tagline:
    "맥에서 받은 한글 파일명이 'ㅍㅏㅇㅣㄹ'처럼 자모 분리되어 보일 때, 폴더·파일을 끌어다 놓으면 정상 이름으로 일괄 교정합니다.",
  category: "desktop",
  status: "active",
  icon: "Languages",
  logo: "/tools/jamo-fixer/logo.png",
  featured: false,
  hasGuide: false,
  screenshot: "/tools/jamo-fixer/card.png",
  downloadUrl:
    "https://github.com/yujeong0411/JamoFixer/releases/latest/download/JamoFixer.exe",
  githubUrl: "https://github.com/yujeong0411/JamoFixer",
  issueUrl: "https://github.com/yujeong0411/JamoFixer/issues",
  quickStart: [
    "JamoFixer.exe를 다운로드해서 더블클릭하세요.",
    "PC 보호창이 뜨면 추가정보를 누르고 실행을 누르세요.",
    "교정할 폴더나 파일을 창에 끌어다 놓거나, 버튼으로 선택하세요.",
    "미리보기를 확인하고 [변환하기]를 누르세요.",
  ],
  features: [
    {
      icon: "Wand2",
      title: "NFC 자동 정규화",
      desc: "유니코드 NFD → NFC 변환으로 깨진 이름 복구",
    },
    {
      icon: "Files",
      title: "폴더·파일 드래그앤드롭",
      desc: "여러 개를 던져도 한 번에 누적 처리",
    },
    {
      icon: "Eye",
      title: "변환 전 미리보기",
      desc: "바뀔 이름을 표로 확인한 뒤 실행",
    },
    {
      icon: "FolderTree",
      title: "하위 폴더 포함",
      desc: "체크박스 한 번으로 전체 재귀 스캔",
    },
    {
      icon: "ShieldCheck",
      title: "안전한 처리 순서",
      desc: "파일 먼저, 폴더는 깊은 순 — 경로 깨짐 방지",
    },
    {
      icon: "Lock",
      title: "오프라인 동작",
      desc: "네트워크 없이 내 컴퓨터에서만 실행",
    },
  ],
  requirements: [
    "Windows 10 이상",
    "디스크 공간 약 50MB",
  ],
  blogPosts: [],
  changelog: [
    {
      version: "1.0.0",
      date: "2026.06.06",
      note: "최초 정식 릴리스. NFC 자동 정규화, 폴더·파일 드래그앤드롭(다중 누적), 미리보기 표, 하위 폴더 재귀, 충돌·rename 오류 안전 처리, 결과 상세 다이얼로그",
    },
  ],
};
