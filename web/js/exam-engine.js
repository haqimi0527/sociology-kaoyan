// ===== 社会学模拟测试引擎 =====
// 两个模式：auto（AI仿学校风格出题）、real（历年真题）
// 引用本文件前需先加载 concepts.json / exams.json / schools.json

var EXAM_CONFIG = {
  school: 'ruc',
  mode: 'auto', // 'auto' | 'real'
  year: 2025,
  count: 10,
  types: ['名词解释', '简答', '论述'],
  duration: 180, // minutes
  difficulty: 'mixed' // 'basic' | 'mixed' | 'advanced'
};

var examBank = [];    // loaded from exams.json
var schoolConfig = {}; // loaded from schools.json
var examPrompts = {};  // loaded from exam-prompts.json

// ===== 加载题库数据 =====
async function loadExamBank() {
  try {
    var resp = await fetch('data/exams.json?v=1');
    examBank = await resp.json();
    console.log('题库加载完成：' + examBank.length + ' 道真题');
  } catch(e) {
    console.warn('题库加载失败，仅支持自主出题模式', e);
    examBank = [];
  }
}

// ===== 模式一：AI 自主出题 =====
async function generateAIExam(schoolId, count, types, difficulty) {
  var prompts = examPrompts.stylePrompts || {};
  var style = prompts[schoolId] || prompts['general'] || {};
  var schoolName = style.schoolName || '通用';

  // 从概念池中按高频权重抽概念
  var pool = concepts.filter(function(c) {
    var ch = c.chapter || '';
    return ch.indexOf('理论/') === 0 || ch.indexOf('社会学研究方法/') === 0 || ch.indexOf('方法/') === 0;
  });
  
  // 优先高频
  var highPool = pool.filter(function(c) { return c.exam_frequency === 'high'; });
  if (highPool.length >= count * 3) pool = highPool;
  
  // 随机打乱取 count*2 个概念（备用）
  _shuffle(pool);
  var selectedConcepts = pool.slice(0, count * 2);

  // 为每个概念准备上下文
  var conceptContext = selectedConcepts.map(function(c) {
    return {
      term: c.term,
      definition: (c.definition || '').slice(0, 200),
      proponent: c.proponent || '',
      chapter: c.chapter || '',
      corePoints: (c.core_points || []).slice(0, 4)
    };
  });

  // 构建 DeepSeek prompt
  var systemPrompt = (style.generatePrompt || prompts.general.generatePrompt) +
    '\n\n要求：\n- 题型分布：' + types.join('、') + '\n- 题目数量：' + count + ' 题\n- 难度：' + difficulty + '\n- 覆盖时期：古典/现代/当代均衡分布';

  var userPrompt = '请根据以下概念列表生成一套完整的' + schoolName + '风格模拟题。\n\n概念列表：\n' +
    JSON.stringify(conceptContext, null, 2) +
    '\n\n返回JSON格式：{"title":"试卷标题","totalScore":150,"questions":[{"type":"名词解释|简答|论述","number":1,"question":"题目原文","score":5,"term":"涉及的概念名","conceptId":"概念id"}]}';

  // 调 DeepSeek
  var apiKey = DEFAULT_API_KEY;
  try {
    var raw = localStorage.getItem('socio_apikey_v1');
    if (raw) { var data = JSON.parse(raw); if (data.key) apiKey = data.key; }
  } catch(e) {}

  var resp = await fetch('https://api.deepseek.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + apiKey },
    body: JSON.stringify({
      model: 'deepseek-chat',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.4,
      max_tokens: 4000
    })
  });

  if (!resp.ok) throw new Error('DeepSeek API ' + resp.status);
  var dsResp = await resp.json();
  var content = dsResp.choices[0].message.content;

  // 解析 AI 返回的 JSON
  var clean = content.replace(/```json\n?/g, '').replace(/```/g, '').trim();
  var examData = JSON.parse(clean);

  // 补充概念引用
  examData.questions = examData.questions.map(function(q) {
    if (q.term) {
      var match = concepts.find(function(c) { return c.term === q.term; });
      if (match) {
        q.concept = match;
        q.conceptId = match.id;
      }
    }
    return q;
  });

  return examData;
}

// ===== 模式二：历年真题 =====
function getRealExam(schoolId, year, types) {
  var schoolName = (function() {
    var sc = (schoolConfig.schools || []).find(function(s) { return s.id === schoolId; });
    return sc ? sc.name : schoolId;
  })();

  // 筛选该学校该年份的题目
  var questions = examBank.filter(function(q) {
    return q.school === schoolName && q.year === year;
  });

  if (!questions.length) {
    // 如果该年没有题，找最近一年的
    var years = examBank
      .filter(function(q) { return q.school === schoolName; })
      .map(function(q) { return q.year; })
      .filter(function(y, i, arr) { return arr.indexOf(y) === i; })
      .sort(function(a, b) { return b - a; });

    if (years.length) {
      year = years[0];
      questions = examBank.filter(function(q) { return q.school === schoolName && q.year === year; });
    }
  }

  if (!questions.length) return null;

  // 按题型筛选
  if (types && types.length) {
    questions = questions.filter(function(q) { return types.indexOf(q.type) !== -1; });
  }

  // 按题号排序
  questions.sort(function(a, b) { return a.number - b.number; });

  // 计算总分
  var totalScore = questions.reduce(function(sum, q) {
    return sum + (q.score != null ? q.score : (q.type === '名词解释' ? 5 : q.type === '简答' ? 10 : q.type === '论述' ? 20 : q.type === '计算' ? 10 : q.type === '单选' ? 2 : q.type === '多选' ? 2 : q.type === '判断' ? 2 : q.type === '选择' ? 2 : q.type === '填空' ? 2 : q.type === '分析' ? 10 : q.type === '辨析' ? 10 : 5));
  }, 0);

  return {
    title: year + '年' + schoolName + '社会学考研真题',
    totalScore: totalScore,
    school: schoolId,
    year: year,
    questions: questions.map(function(q) {
      // 尝试匹配概念
      var match = concepts.find(function(c) {
        return c.term === q.question || (q.question && q.question.indexOf(c.term) !== -1);
      });
      return {
        type: q.type,
        number: q.number,
        question: q.question,
        score: q.score != null ? q.score : (q.type === '名词解释' ? 5 : q.type === '简答' ? 10 : q.type === '论述' ? 20 : q.type === '计算' ? 10 : q.type === '单选' ? 2 : q.type === '多选' ? 2 : q.type === '判断' ? 2 : q.type === '选择' ? 2 : q.type === '填空' ? 2 : q.type === '分析' ? 10 : q.type === '辨析' ? 10 : 5),
        term: match ? match.term : null,
        concept: match || null,
        conceptId: match ? match.id : null
      };
    })
  };
}

// ===== 获取某学校的可用年份列表 =====
function getAvailableYears(schoolId) {
  var schoolName = (function() {
    var sc = (schoolConfig.schools || []).find(function(s) { return s.id === schoolId; });
    return sc ? sc.name : schoolId;
  })();

  return examBank
    .filter(function(q) { return q.school === schoolName; })
    .map(function(q) { return q.year; })
    .filter(function(y, i, arr) { return arr.indexOf(y) === i; })
    .sort(function(a, b) { return b - a; }); // 最新在前
}

// ===== 开始模拟测试（统一入口）=====
async function startSimulationTest(config) {
  EXAM_CONFIG = Object.assign(EXAM_CONFIG, config || {});

  var examData;
  
  if (EXAM_CONFIG.mode === 'auto') {
    // AI 出题
    showToast('🤖 正在生成 ' + (config.schoolName || '') + ' 风格模拟题...');
    try {
      examData = await generateAIExam(
        EXAM_CONFIG.school,
        EXAM_CONFIG.count,
        EXAM_CONFIG.types,
        EXAM_CONFIG.difficulty
      );
    } catch(e) {
      showToast('AI 出题失败：' + e.message, 'error');
      return;
    }
  } else {
    // 历年真题
    examData = getRealExam(EXAM_CONFIG.school, EXAM_CONFIG.year, EXAM_CONFIG.types);
    if (!examData) {
      showToast('该年份暂无真题数据，已选最近年份', 'error');
      return;
    }
  }

  if (!examData || !examData.questions.length) {
    showToast('未能生成题目，请重试', 'error');
    return;
  }

  // 转换为 examState 格式（复用现有考试界面）
  var questions = examData.questions.map(function(q) {
    var qPrompt;
    if (q.type === '名词解释') {
      qPrompt = q.question;
    } else if (q.type === '简答') {
      qPrompt = q.question;
    } else if (q.type === '论述') {
      qPrompt = q.question;
    } else {
      qPrompt = q.question;
    }

    return {
      id: q.conceptId || ('q_' + Math.random().toString(36).slice(2)),
      term: q.term || '',
      type: q.type,
      prompt: qPrompt,
      score: q.score,
      concept: q.concept || null,
      answer: ''
    };
  });

  examState = {
    questions: questions,
    timeLimit: (EXAM_CONFIG.duration || 180) * 60,
    timeLeft: (EXAM_CONFIG.duration || 180) * 60,
    timerId: null,
    startTime: Date.now(),
    examData: examData // 保存原始数据用于显示
  };

  // 渲染考试界面
  var session = document.getElementById('examSession');
  if (session) session.classList.add('active');
  var config = document.getElementById('examConfig');
  if (config) config.style.display = 'none';
  var score = document.getElementById('examScore');
  if (score) score.style.display = 'none';

  renderExamQuestions();
  startExamTimer();
  showToast('📝 考试开始！共 ' + questions.length + ' 题');
}
