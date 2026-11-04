"""Default category scheme: ordered (category, strong patterns, weak patterns).

First matching category in scoring order wins. Ported from a pipeline that was
hand-tuned on a 10,000+ mixed research/book/admin PDF corpus.
Custom categories (from config) are prepended and take priority.
"""

DEFAULT_RULES = [
 # ---- documents / non-reading material ----
 ('travel_bookings', [
   r'boarding pass|boardingpass|itinerary|e-ticket|booking\.com|flight ticket|登机牌|值机|行程单|alitrip|hotel reservation',
   r'\bticket\b|billetter|passenger name record|PNR\b',
 ], [r'booking|ticket']),
 ('certificates_ids', [
   r'passport|visa application|opholdstilladelse|residence permit|identity card',
   r'diploma|certificate of|kursusbevis|deltagerbevis|bevis for|attest|transcript|成绩单|毕业证',
   r'indfødsret|medborgerskabsprøve',
 ], [r'certificate|certificat']),
 ('insurance_pension', [
   r'forsikring|forsikringsbetingelser|insurance policy|policenummer|insurance certificate',
   r'pension|livsforsikring|aldersopsparing',
 ], [r'forsikring|pension']),
 ('bank_tax', [
   r'bank statement|årsopgørelse|forskudsopgørelse|skattekort|skattestyrelsen|skatteforvaltningen',
   r'bankkonto|netbank|afregningsnota|dividends?|udbytte|tax return|taxation',
   r'lønseddel|lønspecifikation|pay ?slip|salary statement|对账单|交易明细|余额宝|transactions_export|share dividends',
 ], [r'skat|bank|løn']),
 ('bills_utilities', [
   r'\bregning\b|faktura|invoice|kvittering|receipt|forbrugsopgørelse',
   r'norlys|energi|elpris|vandmåler|fjernvarme|telefoni|mobilabonnement|telenor|telia',
   r'husleje|lejeafregning|opvarmning',
 ], [r'regning|faktura|kvittering']),
 ('contracts_agreements', [
   r'lejekontrakt|lejeaftale|rental agreement|tenancy|lease\b|huslejekontrakt',
   r'license agreement|non-disclosure|\bNDA\b|terms (and|&) conditions|terms of sale',
   r'kontrakt|aftale mellem|fuldmagt|power of attorney|travel policy|employee handbook',
 ], [r'contract|kontrakt|agreement|aftale']),
 ('misc_admin', [
   r'autosvar|e-mail from|gmail -|ordrebekræftelse|order confirmation|din ordre',
   r'kvittering for|qr-koden|portokoder',
 ], [r'admin']),
 # ---- career ----
 ('career_interview', [
   r'dear (sir|madam|sirs)|i am writing to (you )?(for|to) appl|applying for the position',
   r'curriculum vitae|my resume|enclosed (is|my) (my )?(cv|resume)|resume 样本',
   r'job (interview|hunt|search|offer)|interview (question|answer|secrets|tips|skills)|cover letter',
   r'career (advice|develop|coach|planning)|salary negotia|reference letter|anbefaling',
   r'面试|简历|求职',
 ], [r'\bcv\b|resume|interview']),
 # ---- danish education ----
 ('danish_education', [
   r'opgave \d|tekst ?\d|inspirationsmateriale|teksthæfte|prøve i dansk|studieprøven',
   r'\bhhx\b|\bhf\b|\bstx\b|eksamen|aflevering|opgavesæt|fvu|danskfag',
   r'analyse (model|af)|fortolkning|essay (skriv|model)|samfundsfag',
   r'matematik [ab]\b|lærebog',
 ], [r'opgave|eksamen|dansk']),
 # ---- speech ----
 ('speech_recognition', [
   r'speech (recognition|recogniz)|automatic speech recognition|\bASR\b|keyword spotting',
   r'language model|lattice|decoding graph|phoneme recognition|word error rate|transcription',
   r'hidden markov.*speech|GMM-HMM|end-to-end speech',
 ], []),
 ('speech_synthesis', [
   r'text.?to.?speech|speech synthesis|speech synth|voice conversion|unit selection|parametric speech',
   r'\bTTS\b|synthesized speech|formant synthesis',
 ], []),
 ('speech_analysis', [
   r'speech (quality|intelligib|percept|production|analys|rate|signal)|phonet|vowel|formant|articulat|prosody',
   r'speaker (recognition|verification|identificat)|voice (activity|detect)|\bVAD\b|voice identification|whisper',
   r'speech disorders|dysarthri|lombard|speech in noise|paralinguistic|speech emotion',
 ], []),
 # ---- audio ----
 ('audio_coding', [
   r'audio (bit ?rate )?cod|perceptual (audio )?cod|low.bit.rate audio|lossless audio|audio compress',
   r'psychoacoustic model|masking threshold|spectral band replication|\bMP3\b|\bAAC\b|\bAC-?3\b|audio watermark',
   r'speech cod(e|ing)|CELP|error concealment.*audio|packet loss conceal',
 ], []),
 ('audio_effects_reverb', [
   r'artificial reverberat|reverberation algorithm|reverb(erator| effect)|feedback delay network',
   r'audio effects? processing|\bDAFX\b|digital audio effects|delay effect|phaser|flanger|chorus|pitch shift|time stretch|autotune',
 ], []),
 ('audio_measurement', [
   r'audio measure|acoustic measurement|sound (measurement|level) meter|loudness (measure|meter|normali)',
   r'ITU-R BS\.?1770|EBU.*R128|true.?peak|PESQ|POLQA|objective (audio|sound) quality',
   r'subjective (evaluation|test|assessment) of audio|listening test|ABX test|MUSHRA',
   r'measurement (system|microphone|method)|test (signal|system)|impulse measure|sweep measure',
   r'\bAES TD\b|AES standard|sound level|acoustic calibrat',
 ], []),
 ('audio_production_broadcast', [
   r'broadcast|radio (station|program|broadcast)|television sound|tv sound|sound for (tv|film|television|picture)|film sound',
   r'audio (production|postproduction|workstation|streaming)|streaming audio|network audio|audio over (ip|ethernet)',
   r'recording (studio|session|technique)|multitrack|mixing console|live sound',
   r'digital audio workstation|\bDAW\b|podcast|internet radio',
 ], []),
 ('audio_converters_interfaces', [
   r'\bADC\b|\bDAC\b|analog.to.digital|digital.to.analog|a/d converter|d/a converter|sigma.?delta|delta.?sigma',
   r'jitter|dither|quantization noise.*audio|audio converter|sample (rate )?convert|oversampling',
   r'\bS/PDIF\b|\bAES3\b|\bAES/EBU\b|\bMADI\b|usb audio|firewire audio|audio interface|word clock',
 ], []),
 ('microphones_transducers', [
   r'microphone (design|capsule|element|preamplifier|polar pattern|cartridge|selection)',
   r'condenser microphone|electret microphone|dynamic microphone|ribbon microphone|measurement microphone',
   r'microphone preamplifier|contact microphone|head and torso simulator|\bHATS\b',
 ], []),
 ('audio_equalization', [
   r'equali[sz]ation|equali[sz]er|graphic eq|parametric eq|tone control|bass (boost|control)|treble control',
   r'room (equali|correction) eq|auto eq|system equali',
 ], []),
 ('loudspeakers', [
   r'loudspeaker|headphone|earphone|electroacoustic transducer|woofer|tweeter|subwoofer',
   r'bass reflex|crossover filter|speaker (design|system|driver|enclosure|cabinet)|distributed mode',
   r'sound reinforcement|public address|\bPA system|hi-?fi|speakerphone|in-ear',
 ], []),
 ('hearing_aids_audiology', [
   r'hearing (aid|aids|impair|loss|protect|threshold)|audiolog|audiometr|cochlear implant|tinnitus',
   r'auditory (system|perception|scene|model|filter|nerve|masking|attention)|psychoacoustic',
   r'audiometry',
 ], []),
 ('spatial_audio', [
   r'binaural|head.?related (transfer|impulse)|\bHRTF\b|interaural|ambisonic|transaural|crosstalk cancellation',
   r'spatial (audio|sound|hearing|perception|reproduction)|virtual (acoustic|audio|sound)|3.?d sound|sound localiz',
   r'surround sound|stereophonic|stereo (image|enhancement|reproduction)|wave field synthesis|spaciousness|envelopment',
 ], []),
 ('room_acoustics', [
   r'room acoust|acoustic(s)? of (rooms|concert|enclos)|concert hall|auditorium|reverberation time',
   r'room impulse response|\bRIR\b|acoustic (simulation|model|rendering|absorption|material)|absorption coefficient',
   r'acoustic treatment|sound insulation|diffuser|porous absorber',
 ], []),
 ('noise_reduction', [
   r'noise (reduction|cancell|suppress)|noise reducing|de-?nois|speech enhancement|noisy speech',
   r'dereverb|de-?reverb|reverberation (suppress|cancell)|noise estimation|spectral subtraction|noise compensation',
   r'active noise|anti-?noise|noise control|MCRA|minimum statistics',
 ], []),
 ('echo_cancellation', [
   r'echo cancell|echo suppress|acoustic echo|line echo|residual echo|double.?talk|echo path|howling|feedback cancell',
 ], []),
 ('beamforming', [
   r'beam.?form|microphone array|direction of arrival|\bDOA\b|source localization|end.?fire|superdirective|delay.and.sum',
 ], []),
 ('adaptive_filtering', [
   r'adaptive filter|least.?mean.?square|recursive least.?square|affine projection',
   r'\bLMS\b|\bNLMS\b|\bRLS\b|variable step|proportionate|diffusion (LMS|RLS|adaptive)',
 ], []),
 ('music_audio', [
   r'music (transcription|information retrieval|genre|analysis|processing|recording|synthesis|production|composition|perception|recommendation)',
   r'\bMIR\b|melody|chord|beat (detection|tracking)|onset detection|singing|instrument recognition',
   r'audio fingerprint|query by humming',
 ], []),
 ('audio_general', [
   r'audio (signal|system|quality|engineering|equipment|processing|analys|program|archiv|restoration|mastering|format)',
   r'digital audio|sound (quality|recording|design|engineering|system)|audio engineering society',
 ], [r'\baudio\b|sound']),
 # ---- ML / math ----
 ('statistics_probability', [
   r'statistics|statistical (inference|analysis|method|learning|model)|probabilit|bayesian|monte carlo|markov chain',
   r'\bSPSS\b|regression analysis|anova|mixed models|likelihood (ratio|inference)',
   r'nonparametric|kernel density|bootstrap (method|inference)',
 ], [r'statistics|bayesian|probability']),
 ('mathematics_reference', [
   r'matrix cookbook|linear algebra|matrix (theory|analysis|computation)|eigen(value|vector)|numerical (method|recipe|analysis)',
   r'differential geometry|calculus|mathematical (table|reference|formula)|combinatoric|graph theory',
   r'线性代数|数值方法',
 ], [r'mathematic']),
 ('optimization', [
   r'conjugate gradient|steepest descent|quasi.?newton|convex optimi[sz]|linear programming|nonlinear program',
   r'optimization (method|algorithm|technique)|least squares problem|objective function|line search|trust region',
 ], []),
 ('machine_learning', [
   r'machine learning|deep learning|neural network|neural net\b|artificial intelligence|backpropagation|autoencoder',
   r'support vector machine|\bSVM\b|random forest|gradient boosting|k-?means|clustering|reinforcement learning',
   r'pytorch|tensorflow|keras|scikit|机器学习|深度学习|神经网络',
   r'\bICA\b|independent component analysis|blind source separation|\bNMF\b|non.?negative matrix',
   r'bayesian (network|classifier)|decision tree|genetic algorithm|fuzzy|self.organizing|\bRBM\b|\bCNN\b|\bRNN\b|\bLSTM\b|attention mechanism',
 ], [r'learning|neural']),
 # ---- DSP ----
 ('estimation_tracking', [
   r'kalman filter|particle filter|bayesian filter|state estimation|tracking (algorithm|filter)',
   r'estimation theory|parameter estimation|minimum variance|estimator|bayesian estimation',
 ], []),
 ('filter_design', [
   r'(digital |analog )?filter (design|structure|bank)|\bFIR\b|\bIIR\b|biquad|wave digital filter|multirate|polyphase',
   r'decimation|interpolation filter|sample rate conversion|resampling|anti.?aliasing filter|half.?band',
 ], []),
 ('dsp_general', [
   r'digital signal process|\bDSP\b|signal processing|fast fourier|\bFFT\b|discrete (fourier|cosine|wavelet)|z-?transform',
   r'spectral (estim|analys)|window function|sampling (theorem|rate)|aliasing|cepstrum|autocorrelation',
   r'convolution|wavelet|信号处理|数字信号',
 ], [r'signal|fourier|transform']),
 # ---- computing ----
 ('programming_python', [r'python|django|flask|numpy|pandas|matplotlib|jupyter|pyqt|tkinter|python编程'], [r'python']),
 ('programming_cpp', [r'C\+\+|effective c\+\+|template metaprogram|\bSTL\b|boost library'], []),
 ('programming_java', [r'\bjava\b (program|virtual|api|language)|J2EE|spring framework|servlet|\bJSP\b|\bJVM\b'], []),
 ('programming_other', [
   r'\bR\b (language|faq|programming)|\bS-?PLUS\b|\blua\b|\bperl\b|\bruby\b|matlab programming|\blatex\b',
   r'shell script|bash scripting|pro git|git (version control|tutorial)',
 ], []),
 ('software_engineering', [
   r'software (engineering|architect|design|testing|quality|mainten|reuse|pattern|process)',
   r'design pattern|\bUML\b|unified modeling|refactoring|agile|scrum|extreme programming|unit test',
   r'object.?oriented|软件工程|设计模式|面向对象',
 ], []),
 ('operating_systems', [
   r'\blinux\b|\bunix\b|debian|ubuntu|freebsd|kernel|shell (script|command)|\bbash\b|operating system|posix|system call|device driver',
   r'gdb|gcc|makefile|\bGNU\b|man page|graphviz|libarchive|操作系统',
 ], []),
 ('networking', [
   r'\bTCP/?IP\b|network (protocol|programming|security|architecture|routing)|socket program|router|ethernet',
   r'wireless (LAN|network|communication|sensor)|\bWiFi\b|bluetooth|zigbee|802\.11|\bOFDM\b|\bQAM\b',
   r'\bVPN\b|firewall|cryptograph|encrypt|IPsec|internet protocol|\bIPv[46]|packet|计算机网络|网络协议',
 ], []),
 ('databases', [
   r'database (design|system|management)|\bSQL\b|MySQL|oracle (database|9i|10g|11g)|postgres|sqlite',
   r'data warehouse|business intelligence|data mining|\bOLAP\b|\bETL\b|normalization|数据库',
 ], []),
 ('web_dev', [
   r'web (develop|design|program|application|service|site|page)|\bHTML\b|\bCSS\b|javascript|php\b|ajax|\bXML\b|\bJSON\b',
 ], []),
 ('embedded', [
   r'STM32|STM8|cortex-?m|microcontroller|\bMCU\b|embedded|firmware|bootloader|JTAG|GPIO|\bSPI\b|\bI2C\b|\bUART\b|RTOS',
   r'TMS320|C64x|datasheet|development (board|kit)|Arduino|ESP32|Raspberry|\bFPGA\b|\bVHDL\b|verilog|PCB|schematic',
   r'嵌入式|单片机|开发板|原理图',
 ], []),
 ('rf_microwave', [
   r'antenna|microstrip|microwave|radio frequency|\bRF\b (circuit|design|system|amplifier|filter|power|measurement)|radar',
   r'transmission line|smith chart|scattering parameter|impedance matching|waveguide|\bEMC\b|electromagnetic|hfss',
 ], []),
 ('circuits', [
   r'analog (circuit|design|filter|IC|electronics)|CMOS|op.?amp|operational amplifier|semiconductor|transistor|MOSFET',
   r'circuit (design|analysis|theory|simulation)|power supply|voltage regulator|\bVLSI\b',
 ], []),
 ('video_image', [
   r'image (process|enhanc|segment|compress|restor|quality|denois|retriev)|face recogni|object (detect|track)|edge detection',
   r'video (cod|compress|process|enhanc|quality|track)|\bHEVC\b|H\.26[45]|motion (estimat|compensat)|medical imag|tomograph',
   r'computer vision|depth map|remote sensing',
 ], []),
 # ---- humanities / misc ----
 ('writing_media', [
   r'writing (magazine|fiction|craft|skill|short)|creative writing|journalism|screenwrit|copywrit',
   r'fiction writing|how to write',
 ], []),
 ('fiction', [
   r'novel|novelle|short stor|fairy tale|folklore|小说|童话|poem|digte|poetry',
 ], []),
 ('self_help', [
   r'body language|self.?help|self.?improv|confidence|charisma|persuasion|habit|productivity|time management|mind map|mindfulness',
   r'dating|social (skill|intelligence)|happiness|motivation|口才|情商|励志',
 ], []),
 ('finance_accounting', [
   r'finance|financial|invest(ing|ment)|portfolio|accounting|audit|stock|bond|derivatives|economics|inflation|\bGDP\b',
   r'\bCFA\b|\bCPA\b|注会|金融|会计|投资|股票|证券|财务|审计|经济学|基金|银行',
 ], []),
 ('product_manuals', [
   r"user('s|s)? (guide|manual)|instruction manual|quick (start|install) guide|getting started|brugsanvisning|handbog|使用说明|说明书|用户手册",
 ], []),
 ('misc_reading', [
   r'travel guide|旅行|游记|history book|biography|memoir|philosophy|religion|encyclopedia|百科全书|诗词',
 ], []),
]

# Case-sensitive acronym tokens per category (avoid 'ILD' matching inside 'build').
CASE_SENSITIVE = {
 'speech_recognition': [r'\bASR\b'], 'speech_analysis': [r'\bVAD\b'],
 'dsp_general': [r'\bFFT\b'], 'filter_design': [r'\bFIR\b', r'\bIIR\b'],
 'machine_learning': [r'\bCNN\b', r'\bRNN\b', r'\bLSTM\b', r'\bSVM\b', r'\bICA\b', r'\bNMF\b', r'\bRBM\b'],
 'video_image': [r'\bHEVC\b', r'\bMRI\b'], 'embedded': [r'\bRTOS\b', r'\bGPIO\b', r'\bJTAG\b', r'\bUART\b', r'\bMCU\b'],
 'networking': [r'\bVPN\b', r'\bQAM\b', r'\bOFDM\b'], 'spatial_audio': [r'\bHRTF\b'],
 'finance_accounting': [r'\bCFA\b', r'\bCPA\b'], 'beamforming': [r'\bDOA\b'],
 'microphones_transducers': [r'\bHATS\b'], 'audio_converters_interfaces': [r'\bADC\b', r'\bDAC\b'],
}
