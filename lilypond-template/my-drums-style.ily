\version "2.26.0"

% Money beat: bass drum on beat 1, hi-hat/ride pattern on 2-4.
% \moneyBeat <cymbal-or-hat> <hat-or-ride>
%   first: note on beat 1 with duration (e.g. cymc8 for crash, hh8 for hi-hat)
%   hat:   note for the hat pattern with duration (hh8 for hi-hat, cymr8 for ride)
%
% Durations: bake the duration into each argument (e.g. cymc8, hh8) rather
% than appending it after $var. A bare $hat 8 would render as a whole-note
% hat followed by a separate eighth rest, because $var substitutes a complete
% music expression that already carries its own implicit duration.
%
% Chord durations: in <bd $first > and <sn $hat >, the chord takes the
% duration of its LAST element (the parameter). So bd/sn follow the
% parameter's duration automatically. Keep the fixed drum first and the
% parameter last; reversing the order would make the chord default to a
% whole note.
moneyBeat = #(define-music-function (first hat) (ly:music? ly:music?)
  #{
    \drummode {
      < bd $first > $hat < sn $hat > $hat < bd $hat > $hat < sn $hat > $hat
    }
  #})

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