\version "2.26.0"

#(define my-drums-style
  `(
    (bassdrum        ()           #f           -3)  ; bd
    (snare           ()           #f            1)  ; sn
    (sidestick       cross        #f            1)  ; ss
    (lowfloortom     ()           #f           -2)  ; tomfl
    (highfloortom    ()           #f           -1)  ; tomfh
    (lowtom          ()           #f            0)  ; toml
    (lowmidtom       ()           #f            2)  ; tomml
    (himidtom        ()           #f            3)  ; tommh
    (hightom         ()           #f            4)  ; tomh
    (hihat           cross        #f            5)  ; hh
    (closedhihat     cross        stopped       5)  ; hhc
    (openhihat       xcircle      #f            5)  ; hho
    (halfopenhihat   xcircle      #f            5)  ; hhho
    (pedalhihat      cross        #f           -5)  ; hhp
    (ridecymbal      cross        #f            6)  ; cymr
    (ridebell        mi           #f            6)  ; rb
    (crashcymbal     cross        #f            7)  ; cymc
    (chinesecymbal   mensural     #f            7)  ; cymch
    (splashcymbal    diamond      #f            5)  ; cyms
    (cowbell         triangle     #f            3)  ; cb
    (tambourine      ()           #f            5)  ; tamb
    (claves          ()           #f            5)  ; cl
    (maracas         ()           #f            5)  ; mar
    (triangle        cross        #f            5)  ; tri
   ))

#(define my-drum-pitches
  `((bassdrum        . ,(ly:make-pitch -2 0 NATURAL))
    (snare           . ,(ly:make-pitch -2 2 DOUBLE-FLAT))
    (sidestick       . ,(ly:make-pitch -2 0 SHARP))
    (lowfloortom     . ,(ly:make-pitch -2 3 NATURAL))
    (highfloortom    . ,(ly:make-pitch -2 4 NATURAL))
    (lowtom          . ,(ly:make-pitch -2 5 NATURAL))
    (lowmidtom       . ,(ly:make-pitch -2 6 NATURAL))
    (himidtom        . ,(ly:make-pitch -1 0 NATURAL))
    (hightom         . ,(ly:make-pitch -1 1 NATURAL))
    (hihat           . ,(ly:make-pitch -2 4 FLAT))
    (closedhihat     . ,(ly:make-pitch -2 3 SHARP))
    (openhihat       . ,(ly:make-pitch -2 5 SHARP))
    (halfopenhihat   . ,(ly:make-pitch -2 5 SHARP))
    (pedalhihat      . ,(ly:make-pitch -2 4 SHARP))
    (ridecymbal      . ,(ly:make-pitch -1 2 FLAT))
    (ridebell        . ,(ly:make-pitch -1 3 NATURAL))
    (crashcymbal     . ,(ly:make-pitch -1 1 FLAT))
    (chinesecymbal   . ,(ly:make-pitch -1 2 NATURAL))
    (splashcymbal    . ,(ly:make-pitch -1 4 NATURAL))
    (cowbell         . ,(ly:make-pitch -1 4 SHARP))
    (tambourine      . ,(ly:make-pitch -1 3 SHARP))
    (claves          . ,(ly:make-pitch 1 1 SHARP))
    (maracas         . ,(ly:make-pitch 0 5 SHARP))
    (triangle        . ,(ly:make-pitch 1 4 DOUBLE-SHARP))
   ))