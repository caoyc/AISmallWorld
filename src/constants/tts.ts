// 豆包TTS音色列表（照抄SillyTavern的实现）
export interface DoubaoVoice {
  id: string
  name: string
  gender: 'male' | 'female'
}

export const DOUBAO_VOICES: DoubaoVoice[] = [
  // 通用场景
  { id: 'BV700_V2_streaming', name: '灿灿 2.0', gender: 'female' },
  { id: 'BV705_streaming', name: '炀炀', gender: 'male' },
  { id: 'BV701_V2_streaming', name: '擎苍 2.0', gender: 'male' },
  { id: 'BV001_V2_streaming', name: '通用女声 2.0', gender: 'female' },
  { id: 'BV700_streaming', name: '灿灿', gender: 'female' },
  { id: 'BV406_V2_streaming', name: '超自然音色-梓梓2.0', gender: 'female' },
  { id: 'BV406_streaming', name: '超自然音色-梓梓', gender: 'female' },
  { id: 'BV407_V2_streaming', name: '超自然音色-燃燃2.0', gender: 'male' },
  { id: 'BV407_streaming', name: '超自然音色-燃燃', gender: 'male' },
  { id: 'BV001_streaming', name: '通用女声', gender: 'female' },
  { id: 'BV002_streaming', name: '通用男声', gender: 'male' },
  // 有声阅读
  { id: 'BV701_streaming', name: '擎苍', gender: 'male' },
  { id: 'BV123_streaming', name: '阳光青年', gender: 'male' },
  { id: 'BV120_streaming', name: '反卷青年', gender: 'male' },
  { id: 'BV119_streaming', name: '通用赘婿', gender: 'male' },
  { id: 'BV115_streaming', name: '古风少御', gender: 'female' },
  { id: 'BV107_streaming', name: '霸气青叔', gender: 'male' },
  { id: 'BV100_streaming', name: '质朴青年', gender: 'male' },
  { id: 'BV104_streaming', name: '温柔淑女', gender: 'female' },
  { id: 'BV004_streaming', name: '开朗青年', gender: 'male' },
  { id: 'BV113_streaming', name: '甜宠少御', gender: 'female' },
  { id: 'BV102_streaming', name: '儒雅青年', gender: 'male' },
  // 智能助手
  { id: 'BV405_streaming', name: '甜美小源', gender: 'female' },
  { id: 'BV007_streaming', name: '亲切女声', gender: 'female' },
  { id: 'BV009_streaming', name: '知性女声', gender: 'female' },
  { id: 'BV419_streaming', name: '诚诚', gender: 'male' },
  { id: 'BV415_streaming', name: '童童', gender: 'male' },
  { id: 'BV008_streaming', name: '亲切男声', gender: 'male' },
  // 视频配音
  { id: 'BV408_streaming', name: '译制片男声', gender: 'male' },
  { id: 'BV426_streaming', name: '懒小羊', gender: 'female' },
  { id: 'BV428_streaming', name: '清新文艺女声', gender: 'female' },
  { id: 'BV403_streaming', name: '鸡汤女声', gender: 'female' },
  { id: 'BV158_streaming', name: '智慧老者', gender: 'male' },
  { id: 'BV157_streaming', name: '慈爱姥姥', gender: 'female' },
  { id: 'BR001_streaming', name: '说唱小哥', gender: 'male' },
  { id: 'BV410_streaming', name: '活力解说男', gender: 'male' },
  { id: 'BV411_streaming', name: '影视解说小帅', gender: 'male' },
  { id: 'BV437_streaming', name: '解说小帅-多情感', gender: 'male' },
  { id: 'BV412_streaming', name: '影视解说小美', gender: 'female' },
  { id: 'BV159_streaming', name: '纨绔青年', gender: 'male' },
  { id: 'BV418_streaming', name: '直播一姐', gender: 'female' },
  { id: 'BV142_streaming', name: '沉稳解说男', gender: 'male' },
  { id: 'BV143_streaming', name: '潇洒青年', gender: 'male' },
  { id: 'BV056_streaming', name: '阳光男声', gender: 'male' },
  { id: 'BV005_streaming', name: '活泼女声', gender: 'female' },
  // 特色音色
  { id: 'BV064_streaming', name: '小萝莉', gender: 'female' },
  { id: 'BV051_streaming', name: '奶气萌娃', gender: 'female' },
  { id: 'BV063_streaming', name: '动漫海绵', gender: 'male' },
  { id: 'BV417_streaming', name: '动漫海星', gender: 'female' },
  { id: 'BV050_streaming', name: '动漫小新', gender: 'male' },
  { id: 'BV061_streaming', name: '天才童声', gender: 'male' },
  // 广告配音
  { id: 'BV401_streaming', name: '促销男声', gender: 'male' },
  { id: 'BV402_streaming', name: '促销女声', gender: 'female' },
  { id: 'BV006_streaming', name: '磁性男声', gender: 'male' },
  // 新闻播报
  { id: 'BV011_streaming', name: '新闻女声', gender: 'female' },
  { id: 'BV012_streaming', name: '新闻男声', gender: 'male' },
  // 教育场景
  { id: 'BV034_streaming', name: '知性姐姐-双语', gender: 'female' },
  { id: 'BV033_streaming', name: '温柔小哥', gender: 'male' },
]

// 默认音色（照抄SillyTavern，使用灿灿）
export const DEFAULT_VOICE = 'BV700_streaming'

