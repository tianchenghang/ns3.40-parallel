%==================================================
%% NJUPT-Dissertation-grd.cls for NJUPT Dissertation
%%==================================================

\RequirePackage{amsmath,amsthm,amsfonts,amssymb,bm,mathrsfs,algpseudocode,algorithm}
\RequirePackage{graphicx,float}
\RequirePackage{setspace}   %设置行间距离
\RequirePackage{upgreek}    %直立希腊字母字体
\RequirePackage{makecell}
%\usepackage[algo2e,ruled,noline,linesnumbered]{algorithm2e}
\usepackage{supertabular}
\usepackage{makecell}
\usepackage{diagbox}
%\usepackage{enumerate}
%\usepackage[shortlabels]{enumitem}
%\usepackage{algorithm}
%\usepackage{algorithmic}
%\usepackage{}
%\newcommand{\upcite}[1]{{\setcitestyle{square,super}\cite{#1}}}
%\usepackage[backend=bibtex]{biblatex}
%\usepackage[style==GBT7714-2005NLang]{biblatex}



%\RequirePackage[sort&compress,numbers]{natbib}
%% 上标引用
%\newcommand{\upcite}[1]{\textsuperscript{\cite{#1}}}

\NeedsTeXFormat{LaTeX2e}[2005/12/01]
\ProvidesClass{NJUPT-thesis-grd}[2018/03/25 v1.2 NJUPT-thesis-grd document class]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{ctexbook}}
\newif\ifNJUPT@master\NJUPT@masterfalse
\newif\ifNJUPT@doctor\NJUPT@doctorfalse
\newif\ifNJUPT@istwoside\NJUPT@istwosidefalse
\DeclareOption{twoside}{\NJUPT@istwosidetrue}
\DeclareOption{master}{\NJUPT@mastertrue}
\DeclareOption{doctor}{\NJUPT@doctortrue}

\ProcessOptions\relax
\ifNJUPT@istwoside
\LoadClass[zihao=-4,a4paper,twoside,openright,UTF8,space=auto]{ctexbook}
\else
\LoadClass[zihao=-4,a4paper,oneside,openany,UTF8,space=auto]{ctexbook}
\fi

%% the setup of ctex package
\def\contentsname{目\quad 录}
\def\listfigurename{插图索引}
\def\listtablename{表格索引}

%% 中文封面标题
\def\NJUPT@label@classification{中图分类号：}
\def\NJUPT@label@confidential{密~~~~级：}
\def\NJUPT@label@UDC{UDC分类号：}
\def\NJUPT@label@serialnumber{编号}
\def\NJUPT@label@institutenumber{单位代码：}
\def\NJUPT@label@thesis{学位论文}
\def\NJUPT@label@major{专{\kern 2.4pt}业{\kern 2.4pt}学{\kern 2.4pt}位{\kern 2.4pt}类{\kern 2.4pt}别}
\def\NJUPT@label@title{论文题目：}
\def\NJUPT@label@author{姓~~~~~~~~~~~~~~~~~~~~名}
\def\NJUPT@label@studentnumber{学~~~~~~~~~~~~~~~~~~~~号}
\def\NJUPT@label@advisor{导~~~~~~~~~~~~~~~~~~~~师}
\def\NJUPT@label@degree{专{\kern 2.4pt}业{\kern 2.8pt}{\kern 2.8pt}{\kern 2.8pt}（领 {\kern 2.4pt}域）}
\def\NJUPT@label@submitdate{论文提交日期}
\def\NJUPT@label@defenddate{论{\kern 2.4pt}文{\kern 2.4pt}提{\kern 2.4pt}交{\kern 2.4pt}日{\kern 2.4pt}期}
\def\NJUPT@label@institute{学~~~~院~~~~名~~~~称}
\def\NJUPT@label@interest{类~~~~~~~~~~~~~~~~~~~~型}
\def\NJUPT@label@school{申{\kern 2.4pt}请{\kern 2.4pt}学{\kern 2.4pt}位{\kern 2.4pt}类{\kern 2.4pt}别}

%% 中文封面内容
\def\NJUPT@value@classification{}
\def\NJUPT@value@confidential{}
\def\NJUPT@value@UDC{}
\def\NJUPT@value@serialnumber{}
\def\NJUPT@value@institutenumber{}
\def\NJUPT@value@school{}
\def\NJUPT@value@degree{}
\def\NJUPT@value@title{~~~~~（论~文~题~目）~~~~~}
\def\NJUPT@value@titlemark{\NJUPT@value@title}
\def\NJUPT@value@author{（姓~名）}
\def\NJUPT@value@advisor{（姓名、专业技术职务、学位）}
\def\NJUPT@value@advisorinstitute{（单位）}
\def\NJUPT@value@major{}
\def\NJUPT@value@interest{}
\def\NJUPT@value@studentnumber{}
\def\NJUPT@value@submitdate{}
\def\NJUPT@value@defenddate{}
\def\NJUPT@value@institute{}
\def\NJUPT@value@chairman{}
\def\NJUPT@label@statement{}

%% 设置圆圈的格式 或使用\textcircled
\usepackage{tikz}
\usepackage{etoolbox}
\newcommand{\circled}[2][]{\tikz[baseline=(char.base)]
    {\node[shape = circle, draw, inner sep = 1pt]
    (char) {\phantom{\ifblank{#1}{#2}{#1}}};
    \node at (char.center) {\makebox[0pt][c]{#2}};}}
\robustify{\circled}

%% 论文原创性声明
\def\NJUPT@label@original{南京邮电大学学位论文原创性声明}
\def\NJUPT@label@authorization{南京邮电大学学位论文使用授权声明}
\def\NJUPT@label@underfraduatenumber{研究生学号：}
\def\NJUPT@label@authorsign{研究生签名：}
\def\NJUPT@label@Supervisorsign{导师签名：}
\def\NJUPT@label@originalDate{日期：}
\def\NJUPT@label@originalcontent{\NJUPTspace\NJUPTspace 本人声明所呈交的学位论文是我个人在导师指导
下进行的研究工作及取得的研究成果。尽我所知，除了文中特别加以标注和致谢的地方外，论文中不包含其他人
已经发表或撰写过的研究成果，也不包含为获得南京邮电大学或其它教育机构的学位或证书而使用过的材料。与
我一同工作的同志对本研究所做的任何贡献均已在论文中作了明确的说明并表示了谢意。
\vspace{2ex}
\par 本人学位论文及涉及相关资料若有不实，愿意承担一切相关的法律责任。}
\def\NJUPT@label@authorizationcontent{\NJUPTspace\NJUPTspace 本人承诺所呈交的学位论文不涉及任何
国家秘密，本人及导师为本论文的涉密责任并列第一责任人。
\par 本人授权南京邮电大学可以保留并向国家有关部门或机构送交论文的复印件和电子文档；允许论文被查阅
和借阅；可以将学位论文的全部或部分内容编入有关数据库进行检索；可以采用影印、缩印或扫描等复制手段保
存、汇编本学位论文。本文电子文档的内容和纸质论文的内容相一致。论文的公布（包括刊登）授权南京邮电大
学研究生院办理。
\par 非国家秘密类涉密学位论文在解密后适用本授权书。}

%% 英语封面标题
\def\NJUPT@label@englishadvisor{Supervisor:}
\def\NJUPT@label@englishstatement{Submitted in total fulfilment
  of the requirements for the degree of \NJUPT@value@englishdegree \\
  in \NJUPT@value@englishmajor}
\def\NJUPT@label@englishauthor{Candidate Name:}
\def\NJUPT@label@englishadvisor{Faculty Mentor:}
\def\NJUPT@label@englishchairman{Chair, Thesis Committee:}
\def\NJUPT@label@englishinstitute{School or Department:}
\def\NJUPT@label@englishdegree{Degree Applied:}
\def\NJUPT@label@englishmajor{Major:}
\def\NJUPT@label@englishschool{Degree by:}
\def\NJUPT@label@englishdate{The Date of Defence:}

%% 英语封面内容
\def\NJUPT@value@englishtitle{(English Title of Thesis)}
\def\NJUPT@value@englishauthor{(Author Name)}
\def\NJUPT@value@englishadvisor{(Supervisor Name)}
\def\NJUPT@value@englishinstitute{(Institute Name)}
\def\NJUPT@value@englishscholl{(NJUPT)}
\def\NJUPT@value@englishchair{(someone)}
\def\NJUPT@value@englishdate{}
\def\NJUPT@value@englishdegree{}
\def\NJUPT@value@englishmajor{}

%%其他特殊含义的标签说明
\def\NJUPT@label@abstract{摘要}
\def\NJUPT@label@abbreabstract{缩略语表}
\def\NJUPT@label@denoabbre{专用术语注释表}
\def\NJUPT@label@englishabstract{Abstract}
\def\NJUPT@label@keywords{关键词：}
\def\NJUPT@label@englishkeywords{Key Words:~}
\def\NJUPT@label@conclusion{结论}
\def\NJUPT@label@appendix{附录}
\def\NJUPT@label@publications{附录B 攻读专业学位硕士期间撰写的论文}
\def\NJUPT@label@publicationsProjects{附录D 攻读专业学位硕士期间参加的科研项目}
\def\NJUPT@label@patent{附录C 攻读专业学位硕士期间申请的专利}
\def\NJUPT@label@projects{附录D 攻读专业学位硕士期间参加的科研项目}
\def\NJUPT@label@ProgramList{附录A 程序清单}
\def\NJUPT@label@reference{参考文献！！！！}
\def\NJUPT@label@thanks{致谢}
\def\NJUPT@value@templateversion{v1.2}

%% label in the head 页眉页脚
\def\NJUPT@label@headschoolname{南京邮电大学专业学位硕士研究生学位论文}

%% 当前模板的版本
\newcommand{\version}{\NJUPT@value@templateversion}

\allowdisplaybreaks[4]

%%==============引用geometry 宏包设置纸张和页面========================
%设置版面:上2cm，下2cm，左2cm，右2cm，页眉1.5cm，页脚0.75cm，装订线0cm
\usepackage[%
paper=a4paper,%纸张采用A4纸
top=2cm,% 上 2cm %
bottom=2cm,% 下 2cm %
left=2cm,% 左 2cm %
right=2cm,% 右 2cm %
headheight=0.5cm,% 页眉 1.5cm %
footskip=0.25cm% 没用页脚,将正文底部到页脚底部的距离 0cm %
]{geometry} % 页面设置 %
%% =================================================================

\parskip 0.5ex plus 0.25ex minus 0.25ex    %段落间距离,ex表示小写字母x的高度
%% Command -- Clear Double Page
\def\cleardoublepage{\clearpage\if@twoside \ifodd\c@page\else
  \thispagestyle{empty}%
  \hbox{}\newpage\if@twocolumn\hbox{}\newpage\fi\fi\fi}
%设置行距，大概为22pt/磅对应
\RequirePackage{setspace}
\setstretch{1.5}

%% 设置章节格式, 宋体小二号加粗居中，行距22磅，与正文或节标题的间距设定为段后间距1行。章序号与章名间空一格。
\ctexset{chapter={
      name = {{第},{章}},
      number = {\chinese{chapter}},
      format = {\centering \bfseries \songti \zihao{-2}},
      %format = {\bfseries \sffamily \centering \zihao{3}},
      pagestyle = {NJUPT@headings},
      beforeskip = 16 bp,
      afterskip = 32 bp,
      fixskip = true,
  }
}
%% 设置一级章节格式， 宋体小三号加粗顶左，行距22磅，与上一节的间距为1行，与下面正文或节标题的段间间距为0.5行。序号与题目间空一格。
\ctexset{section={
  format={\raggedright \bfseries \songti \zihao{-3}},
  %format={\raggedright \bfseries \sffamily \zihao{4}},
  beforeskip = 28bp plus 1ex minus .2ex,
  afterskip = 24bp plus .2ex,
  fixskip = true,
  }
}
%% 设置二级标题格式， 黑体四顶左，行距22磅，与上一节的间距为1行，与下面正文或节标题的段间间距为0.5行。序号与题目间空一格。
\ctexset{subsection={
   format = {\raggedright \heiti \zihao{4}},
   %format = {\raggedright \bfseries \songti \zihao{4}},
   beforeskip =28bp plus 1ex minus .2ex,
   afterskip = 24bp plus .2ex,
   fixskip = true,
   }
}
%% 设置三节标题格式
\ctexset{subsubsection={
      format={\raggedright \heiti \zihao{-4}},
      beforeskip=28bp plus 1ex minus .2ex,
      afterskip=24bp plus .2ex,
      fixskip=true,
  }
}

%% 设定目录格式。目录颜色更改黑色
% \addtocontents{toc}{\protect\hypersetup{hidelinks}}
% \addtocontents{lot}{\protect\hypersetup{hidelinks}}
% \addtocontents{lof}{\protect\hypersetup{hidelinks}}

\addtocontents{toc}{\protect\hypersetup{hidelinks} \songti \zihao{5} }
\addtocontents{lot}{\protect\hypersetup{hidelinks} \songti \zihao{5} }
\addtocontents{lof}{\protect\hypersetup{hidelinks} \songti \zihao{5} }

    \RequirePackage{titletoc}
\titlecontents{chapter}[0pt]{ \songti \zihao{5}\vspace{-5pt}}
    { \bfseries{\songti \thecontentslabel}\hspace{\ccwd}}{\bf}
    {\hspace{.5em}\titlerule*{.}\contentspage }
\titlecontents{section}[2\ccwd]{\songti \zihao{5}\vspace{-5pt}}
    { \songti \thecontentslabel\hspace{\ccwd}}{\bf}
    {\hspace{.5em}\titlerule*{.}\contentspage }
\titlecontents{subsection}[4\ccwd]{\songti \zihao{5}\vspace{-5pt}}
    {\thecontentslabel\hspace{\ccwd}}{}
    {\hspace{.5em}\titlerule*{.}\contentspage }

\titlecontents{figure}[0pt]{ \songti\zihao{5}\vspace{-5pt}}
    {\figurename~\thecontentslabel\quad}{\hspace*{-1.5cm}}
    {\hspace{.5em}\titlerule*{.}\contentspage }

\titlecontents{table}[0pt]{ \songti\zihao{5}\vspace{-5pt}}
    {\tablename~\thecontentslabel\quad}{\hspace*{-1.5cm}}
    {\hspace{.5em}\titlerule*{.}\contentspage }

%% 选择编译
\RequirePackage{ifthen}

%% check pdfTeX mode
\RequirePackage{ifpdf}

%% fancyhdr宏包-页眉页脚控制
\RequirePackage{fancyhdr}

%% 空 页眉页脚
\fancypagestyle{NJUPT@empty}{%
  \fancyhf{}}

\fancypagestyle{NJUPT@abstract}{%
  \fancyhf{}                          % 清空所有页眉页脚
  \fancyfoot[C]{\songti\zihao{-5} \thepage} % 保留页码页脚
  \renewcommand{\headrulewidth}{0pt}  % 去掉页眉横线
}
  %======正文页眉页脚=================

\fancypagestyle{NJUPT@headings}{
    \fancyhf{}
    \renewcommand{\headrulewidth}{0.5pt}
    \fancyfoot[C]{\songti\zihao{-5} \thepage}
    \fancyhead[R]{\songti\zihao{-5} \leftmark}     %页眉右边设置为章节标题
    \fancyhead[L]{\ifNJUPT@master\zihao{-5}{\songti 南京邮电大学专业学位硕士研究生学位论文}     %页眉左边设置为headschoolname
        \else\zihao{-5}{\songti 南京邮电大学专业学位硕士研究生学位论文}\fi}
}

%==================对于openright 选项，必须保证章页右开，且如果前章末页内容须清空其页眉页脚。===================
\let\NJUPT@cleardoublepage\cleardoublepage
\newcommand{\NJUPT@clearemptydoublepage}{%
	\clearpage{\pagestyle{NJUPT@empty}\NJUPT@cleardoublepage}}
\let\cleardoublepage\NJUPT@clearemptydoublepage

%================修该frontmatter 的页码为大写罗马格式，并调整页面风格===============
\renewcommand{\frontmatter}{
 \if@openright\cleardoublepage\else\clearpage\fi
  \@mainmatterfalse
  \pagenumbering{Roman}
  \pagestyle{NJUPT@abstract}
}
%=======================修改mainmatter 的页码为阿拉伯格式，并调整页面风格========================
\renewcommand{\mainmatter}{
  \if@openright\cleardoublepage\else\clearpage\fi
  \@mainmattertrue
  \pagenumbering{arabic}
  \pagestyle{NJUPT@headings}
}


%% 复杂表格
\RequirePackage{threeparttable}
\RequirePackage{dcolumn}
\RequirePackage{multirow}
\RequirePackage{booktabs}
\newcolumntype{d}[1]{D{.}{.}{#1}}% or D{.}{,}{#1} or D{.}{\cdot}{#1}


%% 定义几个常用的数学常量符号
\newcommand{\me}{\mathrm{e}} %定义 对数常数e，虚数符号i,j以及微分算子d为直立体。
\newcommand{\mi}{\mathrm{i}}
\newcommand{\mj}{\mathrm{j}}
\newcommand{\dif}{\,\mathrm{d}}

\theoremstyle{plain}
  \newtheorem{algo}{算法~}[chapter]
  \newtheorem{thm}{定理~}[chapter]
  \newtheorem{lem}[thm]{引理~}
  \newtheorem{prop}[thm]{命题~}
  \newtheorem{cor}[thm]{推论~}
\theoremstyle{definition}
  \newtheorem{defn}{定义~}[chapter]
  \newtheorem{conj}{猜想~}[chapter]
  \newtheorem{exmp}{例~}[chapter]
  \newtheorem{rem}{注~}
  \newtheorem{case}{情形~}
\renewcommand{\proofname}{\bf 证明}

%% 英文字体默认使用 Times New Roman
\RequirePackage{xltxtra} % \XeTeX Logo
\setmainfont{Times New Roman}   % 衬线字体
\setsansfont{Arial}             % 无衬线字体
\setmonofont{Courier New}       % 等宽字体，一般是打印字体
%% 中文字体默认使用宋体
%\setCJKmainfont{songti}
\IfFontExistsTF{STXingkai}{
  \setCJKfamilyfont{hwxk}{STXingkai} % Windows
}{
  \setCJKfamilyfont{hwxk}{Sarasa Gothic SC} % Other
}
\newcommand{\stxk}{\CJKfamily{hwxk}}
\IfFontExistsTF{SimSun}{
  \setCJKfamilyfont{zhsong}[AutoFakeBold = {2.17}]{SimSun} % Windows
}{
  \setCJKfamilyfont{zhsong}[AutoFakeBold = {2.17}]{Sarasa Gothic SC} % Other
}
%\renewcommand{\songti}{\CJKfamily{zhsong}}

%% graphics packages
\RequirePackage{graphicx}
%% 并列子图
\RequirePackage{subfigure}

\RequirePackage{wrapfig}
%%===========================设置图表标题选项==========================
\RequirePackage{amsmath}
\RequirePackage{caption}
%\usepackage{tocloft}
%\renewcommand{\cftfigpresnum}{\bfseries Figure}
\DeclareCaptionLabelSeparator{zhspace}{\hspace{1\ccwd}}
\DeclareCaptionFont{fontsize}{ \zihao{5}}
\captionsetup{
  font = {{fontsize}},
  labelsep = zhspace,
  labelfont = bf,
}
\captionsetup[table]{
  position = top,
  aboveskip = 6bp,
  belowskip = 6bp,
  labelfont = bf,
}
\numberwithin{table}{chapter}
\captionsetup[figure]{
  position = bottom,
  aboveskip = 6bp,
  belowskip = 6bp,
  labelfont = bf,
}

%% 如果插入的图片没有指定扩展名，那么依次搜索下面的扩展名所对应的文件
\DeclareGraphicsExtensions{.pdf,.eps,.png,.jpg,.jpeg}
% ccaption -- bicaption
%\RequirePackage{ccaption}
%\captiondelim{\ }
%\captionnamefont{\songti\zihao{5}}
%\captiontitlefont{\songti\zihao{5}}


%% sort and compress citations
\RequirePackage[numbers,square,comma,super,sort&compress]{natbib}
% 上标引用
\newcommand{\upcite}[1]{\textsuperscript{\cite{#1}}}


%% 水平引用
\RequirePackage{xpatch}
\xpatchcmd\citenum{\NAT@parfalse}{\NAT@partrue}{}


% 将浮动参数设为较宽松的值
\renewcommand{\textfraction}{0.15}
\renewcommand{\topfraction}{0.85}
\renewcommand{\bottomfraction}{0.65}
\renewcommand{\floatpagefraction}{0.60}


% 定公式、图、表编号为"3-1"的形式，即分隔符由.变为短杠
\renewcommand\theequation{\arabic{chapter}.\arabic{equation}}
\renewcommand\thefigure{\arabic{chapter}.\arabic{figure}}
\renewcommand\thetable{\arabic{chapter}.\arabic{table}}

% 颜色宏包
\RequirePackage{xcolor}


% 中文破折号
\newcommand{\cndash}{\rule{0.0em}{0pt}\rule[0.35em]{1.4em}{0.05em}\rule{0.2em}{0pt}}

% listings 源代码显示宏包
\RequirePackage{listings}
\lstset{tabsize=4, %
  frame=shadowbox, %把代码用带有阴影的框圈起来
  commentstyle=\color{red!50!green!50!blue!50},%浅灰色的注释
  rulesepcolor=\color{red!20!green!20!blue!20},%代码块边框为淡青色
  keywordstyle=\color{blue!90}\bfseries, %代码关键字的颜色为蓝色，粗体
  showstringspaces=false,%不显示代码字符串中间的空格标记
  stringstyle=\ttfamily, % 代码字符串的特殊格式
  keepspaces=true, %
  breakindent=22pt, %
  numbers=left,%左侧显示行号
  stepnumber=1,%
  numberstyle=\tiny, %行号字体用小号
  basicstyle=\footnotesize, %
  showspaces=false, %
  flexiblecolumns=true, %
  breaklines=true, %对过长的代码自动换行
  breakautoindent=true,%
  breakindent=4em, %
  aboveskip=1em, %代码块边框
  %% added by http://bbs.ctex.org/viewthread.php?tid=53451
  fontadjust,
  captionpos=t,
  framextopmargin=2pt,framexbottommargin=2pt,abovecaptionskip=-3pt,belowcaptionskip=3pt,
  xleftmargin=4em,xrightmargin=4em, % 设定listing左右的空白
  texcl=true,
  % 设定中文冲突，断行，列模式，数学环境输入，listing数字的样式
  extendedchars=false,columns=flexible,mathescape=true
  numbersep=-1em
}
\renewcommand{\lstlistingname}{代码} %% 重命名Listings标题头


%% hyperref package
\definecolor{navyblue}{RGB}{0,0,0}
\RequirePackage{hyperref}
\hypersetup{
  bookmarksnumbered,%
  linktoc=all,
  colorlinks=true,
  citecolor=navyblue,
  filecolor=cyan,
  linkcolor=navyblue,
  linkbordercolor=navyblue,
  urlcolor=navyblue,
  plainpages=false,%
  pdfstartview=FitH
}

%% enumerate 列表环境间距调节
\usepackage{enumitem}
% \setenumerate[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=5pt}
% \setitemize[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt}
% \setdescription{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=5pt}

%_  参考文献风格 added by wei.jianwen@gmail.com
\bibliographystyle{GBT7714-2005NLang}
%\usepackage[backend=biber,style=gb7714-2015]{biblatex}


%_ NJUPTspace
%\newcommand\NJUPTspace{\protect\CTEX@spaceChar\protect\CTEX@spaceChar}
\newcommand{\NJUPTspace}[1][1]{\hspace{#1\ccwd}}

\def\NJUPT@getfileinfo#1 #2 #3\relax#4\relax{%
  \def\NJUPTfiledate{#1}%
  \def\NJUPTfileversion{#2}%
  \def\NJUPTfileinfo{#3}}%
\expandafter\ifx\csname ver@NJUPTmaster-xetex.cls\endcsname\relax
  \edef\reserved@a{\csname ver@ctextemp_NJUPTmaster-xetex.cls\endcsname}
\else
  \edef\reserved@a{\csname ver@NJUPTmaster-xetex.cls\endcsname}
\fi
\expandafter\NJUPT@getfileinfo\reserved@a\relax? ? \relax\relax
\def\NJUPT@underline[#1]#2{%
  \underline{\hbox to #1{\hfill#2\hfill}}}
\def\NJUPTunderline{\@ifnextchar[\NJUPT@underline\underline}

%%%%中文标题页的可用命令
\newcommand\classification[1]{\def\NJUPT@value@classification{#1}}
\newcommand\studentnumber[1]{\def\NJUPT@value@studentnumber{#1}}
\newcommand\confidential[1]{\def\NJUPT@value@confidential{#1}}
\newcommand\UDC[1]{\def\NJUPT@value@UDC{#1}}
\newcommand\serialnumber[1]{\def\NJUPT@value@serialnumber{#1}}
\newcommand\institutenumber[1]{\def\NJUPT@value@institutenumber{#1}}
\newcommand\school[1]{\def\NJUPT@value@school{#1}}
\newcommand\degree[1]{\def\NJUPT@value@degree{#1}}
\renewcommand\title[2][\NJUPT@value@title]{%
  \def\NJUPT@value@title{#2}
  \def\NJUPT@value@titlemark{\MakeUppercase{#1}}}
\renewcommand\author[1]{\def\NJUPT@value@author{#1}}
\newcommand\advisor[1]{\def\NJUPT@value@advisor{#1}}
\newcommand\advisorinstitute[1]{\def\NJUPT@value@advisorinstitute{#1}}
\newcommand\major[1]{\def\NJUPT@value@major{#1}}
\newcommand\submitdate[1]{\def\NJUPT@value@submitdate{#1}}
\newcommand\defenddate[1]{\def\NJUPT@value@defenddate{#1}}
\newcommand\institute[1]{\def\NJUPT@value@institute{#1}}
\newcommand\interest[1]{\def\NJUPT@value@interest{#1}}


%% 第一页和第二页
%% “绘制”中文标题页
\renewcommand\maketitle[1]{%
  \cleardoublepage
  \thispagestyle{empty}
  \begin{center}
    \vspace*{60mm}
    {\heiti\zihao{-2} \NJUPT@value@title}
    \vskip 40mm
    {\heiti \zihao{-3} \NJUPT@value@author} %黑体 小三
     \vskip 4mm
    {\heiti \zihao{-3} \NJUPT@value@defenddate} %黑体 小三
  \end{center}
  \clearpage
  \if@twoside
    \thispagestyle{empty}
    \cleardoublepage
  \fi
 }

\newcommand\makeInfo[1]%
 {
  \newpage
  \cleardoublepage
  \thispagestyle{empty}

%udc ltz
{ %
  {\songti \zihao{-4} \noindent \NJUPT@label@institutenumber} \NJUPTunderline[60pt] \NJUPT@value@institutenumber ~
  {\songti \zihao{-4} \NJUPT@label@confidential} \NJUPTunderline[60pt] \NJUPT@value@confidential
}
    \vskip \stretch{0.5}
    \begin{figure}[H]
    \centering
        \includegraphics[width=0.4\textwidth]{coverfig/f1}
    \end{figure}
    \begin{center}
      {\stxk \zihao{-0} 专~~业~~学~~位~~硕~~士~~论~~文}
    \end{center}
    \begin{figure}[H]
    \centering
        \includegraphics[width=0.15\textwidth]{coverfig/f2}
    \end{figure}

   % \begin{center}{
   %  \vskip \stretch{0.5}
   %     {\songti\zihao{-2} \NJUPT@label@title \zihao{3}  \NJUPTunderline[300pt]{\NJUPT@value@title}} \vspace{10pt}
   %     % {\songti\zihao{3} \kern 85pt \NJUPTunderline[70pt]{设计研究}}
   %  \vskip \stretch{0.5}

      \begin{center}{
    \vskip \stretch{0.5}
       {\songti\zihao{-2} \NJUPT@label@title \zihao{3}  \NJUPTunderline[320pt]{\NJUPT@value@title}}
    \vskip \stretch{0.5}



    {\fangsong\zihao{4}}
    \def\tabcolsep{1pt}
    \def\arraystretch{1.5}

	%黑体 小三
    {\heiti\zihao{4}
    \begin{spacing}{1.5}
     \begin{tabular}{l p{3mm} c}
      \NJUPT@label@studentnumber & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@studentnumber}
    \\
      \NJUPT@label@author & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@author}
    \\
      \NJUPT@label@advisor & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@advisor}
    \\
      \NJUPT@label@major & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@major}
    \\
      \NJUPT@label@interest & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@interest}
    \\
      \NJUPT@label@degree & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@degree}
    \\
      \NJUPT@label@defenddate & & \NJUPTunderline[180pt]{\songti\zihao{3} \NJUPT@value@defenddate}
     \end{tabular}
    \end{spacing}}
    }
  \end{center}

  %\vskip \stretch{0.5}
  \clearpage
  \if@twoside
    \thispagestyle{empty}
    \cleardoublepage
  \fi
}

% English Title Page
% 英文标题页可用命令
\newcommand\englishtitle[1]{\def\NJUPT@value@englishtitle{#1}}
\newcommand\englishauthor[1]{\def\NJUPT@value@englishauthor{#1}}
\newcommand\englishadvisor[1]{\def\NJUPT@value@englishadvisor{#1}}
\newcommand\englishschool[1]{\def\NJUPT@value@englishschool{#1}}
\newcommand\englishinstitute[1]{\def\NJUPT@value@englishinstitute{#1}}
\newcommand\englishdate[1]{\def\NJUPT@value@englishdate{#1}}
\newcommand\englishdegree[1]{\def\NJUPT@value@englishdegree{#1}}
\newcommand\englishmajor[1]{\def\NJUPT@value@englishmajor{#1}}
\newcommand\englishchairman[1]{\def\NJUPT@value@englishchairman{#1}}

% "绘制"英文标题页
\newcommand\makeEnglishInfo[1]{%
  \cleardoublepage
  \thispagestyle{empty}

   \begin{center}


   \vspace*{5em}
   %\vskip \stretch{0.5}
    %论文题目	  Times New Roman 二 加粗
   {\zihao{2}\textbf{\NJUPT@value@englishtitle}}
   %\bfseries
   \vskip \stretch{1.0}
   \begin{spacing}{1.5}{
   {\zihao{-2}{Thesis Submitted to Nanjing University of Posts and \\
   Telecommunications for the Degree of \\
   Master of ENGINEERING \\}}}
   \end{spacing}
   \vskip \stretch{0.1}
   \begin{figure}[H]
    \centering
        \includegraphics[width=0.15\textwidth]{coverfig/f2}
   \end{figure}

    \vskip \stretch{0.5}
    % Times New Roman 三
   \begin{spacing}{1.5}
   {\zihao{3} {By
    \\
      {\NJUPT@value@englishauthor}
    \\
      Supervisor:~{\NJUPT@value@englishadvisor}
    \\
      {\NJUPT@value@englishdate} \\}}
    \end{spacing}

  \end{center}

  \vskip \stretch{0.5}
  \clearpage
  \if@twoside
  \thispagestyle{empty}
   \cleardoublepage
  \fi
}

%绘制树立排放的论文题目和学校名称
\newcommand\makeVerticalTitle{
   \cleardoublepage
   \thispagestyle{empty}
   \vskip 5cm
   \begin{center}
    \setstretch{1.1}
    \begin{minipage}{1em}
        {\heiti\zihao{3}\NJUPT@value@vtitle}
        \vskip 2cm
        {\heiti\zihao{3}\NJUPT@value@school}
    \end{minipage}
   \end{center}
    \clearpage
    \if@twoside
        \thispagestyle{empty}
        \cleardoublepage
    \fi}

% 原创性声明
\newcommand\makeDeclareOriginal{%
  \cleardoublepage
  \pdfbookmark[0]{声明}{statement}
  \thispagestyle{empty}
  \begin{center}
  \vspace*{4em}
  {\bf\zihao{-2} \NJUPT@label@original}
  \end{center}
  \vskip 10pt
  {\zihao{-4}\NJUPT@label@originalcontent}
  \vskip 40pt
  {\zihao{-4}\NJUPT@label@underfraduatenumber} \NJUPTunderline[6em]{} \hspace{0.5em}{\zihao{-4}\NJUPT@label@authorsign} \NJUPTunderline[6em]{}
  \hspace{0.5em}{\zihao{-4}\NJUPT@label@originalDate} \NJUPTunderline[6em]{}

  \vskip 30mm

  \begin{center}
  {\bf\zihao{-2} \NJUPT@label@authorization}
  \end{center}
  \vskip 10pt
  {\zihao{-4} \NJUPT@label@authorizationcontent}
  \vskip 40pt

  {\zihao{-4}\NJUPT@label@authorsign} \NJUPTunderline[6em]{} \hspace{0.5em} {\zihao{-4}\NJUPT@label@Supervisorsign} \NJUPTunderline[6em]{} \hspace{0.5em}
  {\zihao{-4}\NJUPT@label@originalDate} \NJUPTunderline[6em]{}
  \vskip 15pt
  %\hspace{8em}{\zihao{4}\NJUPT@label@originalDate} \NJUPTunderline[6em]{} \hspace{2em} {\zihao{4}\NJUPT@label@originalDate} \NJUPTunderline[6em]{}
  \clearpage
  \if@twoside
    \thispagestyle{empty}
    \cleardoublepage
  \fi
}

 % 中文摘要
 \newenvironment{abstract}
 {
  % \cleardoublepage
  \pagestyle{empty}
  \chapter{\NJUPT@label@abstract}
  \thispagestyle{NJUPT@abstract}
  \pagestyle{NJUPT@abstract}

 }


 % % 中文摘要 + 缩写词
 % \newenvironment{abbreabstract}
 % {
 %  % \cleardoublepage
 %  \pagestyle{empty}
 %  \chapter{\NJUPT@label@abbreabstract}
 % }

  % 中文摘要 + 符号 + 缩写词
 \newenvironment{denoabbre}
 {
  % \cleardoublepage
  \pagestyle{NJUPT@headings}
  \chapter{\NJUPT@label@denoabbre}
  \pagestyle{NJUPT@headings}
 }


 {}
%下一页从偶数页开始
 \newcommand\beginatevenpage{
 \clearpage
  \if@twoside
    \cleardoublepage
    \pagestyle{empty}
  \fi
 }
 % 中文摘要关键词
 \newcommand\keywords[1]{%
   \vspace{2ex}\noindent{\bf \songti \NJUPT@label@keywords} #1}

 % 英文摘要
 \newenvironment{englishabstract}
 {
  \clearpage
  \chapter{\NJUPT@label@englishabstract}
  \thispagestyle{NJUPT@abstract}
  \pagestyle{NJUPT@abstract}
 }
 {}

 % 英文摘要关键词
 \newcommand\englishkeywords[1]{%
  \vspace{2ex}\noindent{\bf \NJUPT@label@englishkeywords} #1}


%_ 目录
\renewcommand\tableofcontents{%
  \if@twocolumn
  \@restonecoltrue\onecolumn
  \else
  \@restonecolfalse
  \fi
  \chapter*{\contentsname}%目录里显示“目录”，否则\chapter*
  \@mkboth{\MakeUppercase\contentsname}{\MakeUppercase\contentsname}%
  \pdfbookmark[0]{目录}{NJUPTtoc}
  \thispagestyle{NJUPT@abstract}
  \pagestyle{NJUPT@abstract}
  \@starttoc{toc}%
  \if@restonecol\twocolumn\fi

}

% 正文页眉页脚
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\songti \zihao{5} \NJUPT@label@headschoolname}  % 奇数页左页眉
\fancyfoot[C]{\songti \zihao{5} {\thepage}}      % 页脚


\fancypagestyle{plain}{% 设置开章页页眉页脚风格(只有页码作为页脚)
  \fancyhf{}%
  \fancyhead[L]{\songti \zihao{5} \NJUPT@label@headschoolname}
  \fancyfoot[C]{\songti \zihao{5} ~---~{\thepage}~---~} %%首页页脚格式
}

%_ 参考文献环境
\renewenvironment{thebibliography}[1]
     {\zihao{5}
      \chapter*{\bibname}
      \@mkboth{\MakeUppercase\bibname}{\MakeUppercase\bibname}%
      \addcontentsline{toc}{chapter}{参考文献}
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \setlength{\parsep}{1mm}
            \setlength{\labelsep}{0.5em}
            \setlength{\itemsep}{0.05pc}
            \setlength{\listparindent}{0in}
            \setlength{\itemindent}{0in}
            \setlength{\rightmargin}{0in}
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}

%%发表论文与研究成果清单环境
\newenvironment{publications}[1]
     {\chapter{\NJUPT@label@publications}%
      \@mkboth{\MakeUppercase\NJUPT@label@publications}
              {\MakeUppercase\NJUPT@label@publications}%
      \list{（{\@arabic\c@enumiv}）}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \setlength{\parsep}{1mm}
            \setlength{\labelsep}{0.5em}
            \setlength{\itemsep}{0.05pc}
            \setlength{\listparindent}{0in}
            \setlength{\itemindent}{0in}
            \setlength{\rightmargin}{0in}
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `publications' environment}}%
      \endlist}





%%攻读学位期间参与项目环境
\newenvironment{publicationsProjects}[1]
     {\chapter{\NJUPT@label@publicationsProjects}%
      \@mkboth{\MakeUppercase\NJUPT@label@publicationsProjects}
              {\MakeUppercase\NJUPT@label@publicationsProjects}%
      \list{（{\@arabic\c@enumiv}）}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \setlength{\parsep}{1mm}
            \setlength{\labelsep}{0.5em}
            \setlength{\itemsep}{0.05pc}
            \setlength{\listparindent}{0in}
            \setlength{\itemindent}{0in}
            \setlength{\rightmargin}{0in}
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `publicationsProjects' environment}}%
      \endlist}


%%攻读学位期间申请专利环境
\newenvironment{patent}[1]
     {\chapter{\NJUPT@label@patent}%
      \@mkboth{\MakeUppercase\NJUPT@label@patent}
              {\MakeUppercase\NJUPT@label@patent}%
      \list{（{\@arabic\c@enumiv}）}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \setlength{\parsep}{1mm}
            \setlength{\labelsep}{0.5em}
            \setlength{\itemsep}{0.05pc}
            \setlength{\listparindent}{0in}
            \setlength{\itemindent}{0in}
            \setlength{\rightmargin}{0in}
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `patent' environment}}%
      \endlist}

%%攻读学位期间参与项目环境
\newenvironment{projects}[1]
     {\chapter{\NJUPT@label@projects}%
      \@mkboth{\MakeUppercase\NJUPT@label@projects}
              {\MakeUppercase\NJUPT@label@projects}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `projects' environment}}%
      \endlist}

    \newenvironment{ProgramList}
  {\chapter{\NJUPT@label@ProgramList}}
  {}

\newenvironment{ProgramListsection}[1]
  {{\noindent\normalfont\bfseries #1}
   \list{}{\labelwidth\z@
           \leftmargin 2\ccwd}
   \item\relax}
   {\endlist}

\newenvironment{ProgramListli}[1]
  {{\noindent\normalfont\bfseries #1}
   \list{}{\labelwidth\z@
           \leftmargin 4\ccwd
           \itemindent -2\ccwd
           \listparindent\itemindent}
   \item\relax}
   {\endlist}

\newenvironment{conclusion}
  {\chapter*{结论}
    \@mkboth{结论}{结论}%
    \addcontentsline{toc}{chapter}{结论}}
  {}

\renewenvironment{thanks}
  {\chapter{\NJUPT@label@thanks}
  \songti
  }
  {}

\newenvironment{symbolnote}
  {\chapter{\NJUPT@label@symbolnote}
  \fangsong}
  {}

  %%%============================术语=====================
  \newcommand{\NJUPT@denotation@name}{主要符号注释表}
  \newenvironment{denotation}[1][4cm]{
      \chapter{\NJUPT@denotation@name} % no tocline
      \noindent\begin{list}{}%
      {\vskip-30bp\zihao{-4}
       \renewcommand\makelabel[1]{##1\hfil}
       \setlength{\labelwidth}{#1} % 标签盒子宽度
       \setlength{\labelsep}{0.5cm} % 标签与列表文本距离
       \setlength{\itemindent}{0cm} % 标签缩进量
       \setlength{\leftmargin}{\labelwidth+\labelsep} % 左边界
       \setlength{\rightmargin}{0cm}
       \setlength{\parsep}{0cm} % 段落间距
       \setlength{\itemsep}{0cm} % 标签间距
      \setlength{\listparindent}{0cm} % 段落缩进量
      \setlength{\topsep}{0pt} % 标签与上文的间距
     }}{\end{list}}

  \newcommand{\NJUPT@abbreviation@name}{缩略语表}
  \newenvironment{abbreviation}[1][4cm]{
      \chapter{\NJUPT@abbreviation@name}
      \noindent\begin{list}{}%
      {\vskip-30bp\zihao{-4}
       \renewcommand\makelabel[1]{##1\hfil}
       \setlength{\labelwidth}{#1} % 标签盒子宽度
       \setlength{\labelsep}{0.5cm} % 标签与列表文本距离
       \setlength{\itemindent}{0cm} % 标签缩进量
       \setlength{\leftmargin}{\labelwidth+\labelsep} % 左边界
       \setlength{\rightmargin}{0cm}
       \setlength{\parsep}{0cm} % 段落间距
       \setlength{\itemsep}{0cm} % 标签间距
      \setlength{\listparindent}{0cm} % 段落缩进量
      \setlength{\topsep}{0pt} % 标签与上文的间距
     }}{\end{list}}
%====增加化学、国际单位宏包
     \RequirePackage[version=4]{mhchem}
     \RequirePackage{siunitx}
\setcounter{secnumdepth}{4}  % 章节编号深度 (part 对应 -1)
\setcounter{tocdepth}{2}     % 目录深度 (part 对应 -1)

\endinput
