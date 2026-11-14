\version "2.26.0"

\header {
  title = "Song Title"
  subtitle = ""
  subsubtitle = "Song Subtitle"
  composer = ""
  arranger = "Arranger Name"
  poet = ""
  instrument = ""
  meter = ""
  copyright = ""
  tagline = ""
}

\include "my-drums-style.ily"

music = \drummode {
  \numericTimeSignature
  \time 4/4
  \tempo 4 = 120
  \stemUp

  r2 r4 r8 r8  |
  cymc4 cymr4 rb4 hho4(  |
  hhc4)  hh4  sn4  ss4  |
  tommh  tomml4  tomfh4  bd4  |
  \break

  \grace sn8( sn4) \grace tomml8( tomfh4) \acciaccatura \parenthesize sn8( sn4) \parenthesize sn4  |
  sn2:32 ~ sn2:32 ~  |
  sn2  sn2  |
  sn4:8 sn4-> hhp4 bd4  |
  \break

  \textMark \markup "Money Beat with Repeats"
  \repeat volta 2 {
    <bd cymc>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  |
    \repeat percent 2 { <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  }
    <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  |
  }
  <bd cymc>4 r2. |
  \break

  \textMark \markup "Money Beat with Different Endings"
  \repeat volta 2 {
    <bd cymc>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  |
    \repeat percent 2 { <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  }
  }
  \alternative {
    { <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8 | }
    { <bd cymc>4 r2. | }
  }
  \break

  \textMark \markup "Money Beat with 4 repeats (1,3 same / 2,4 same)"
  \repeat volta 4 {
    <bd cymc>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  |
    \repeat percent 2 { <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8  }
  }
  \alternative {
    \volta 1,3 { <bd hh>8  hh8  <sn hh>8  hh8  <bd hh>8  hh8  <sn hh>8  hh8 | }
    \volta 2,4 { <bd cymc>4 r2. | }
  }
  \break
}

\score {
  \new DrumStaff \with {
    drumStyleTable = #(alist->hash-table my-drums-style)
  } \music
  \layout {
    \context {
      \Score
      \override NonMusicalPaperColumn.line-break-permission = ##f
    }
  }
}

\score {
  \new DrumStaff \with {
    drumStyleTable = #(alist->hash-table my-drums-style)
    drumPitchTable = #(alist->hash-table my-drum-pitches)
  } \unfoldRepeats \music
  \midi { }
}
