(define (domain Dangeon)

    (:requirements
        :typing
        :negative-preconditions
    )

    (:types
        swords cells
    )

    (:predicates
        ;Hero's cell location
        (at-hero ?loc - cells)
        
        ;Sword cell location
        (at-sword ?s - swords ?loc - cells)
        
        ;Indicates if a cell location has a monster
        (has-monster ?loc - cells)
        
        ;Indicates if a cell location has a trap
        (has-trap ?loc - cells)
        
        ;Indicates if a chell or sword has been destroyed
        (is-destroyed ?obj)
        
        ;connects cells
        (connected ?from ?to - cells)
        
        ;Hero's hand is free
        (arm-free)
        
        ;Hero's holding a sword
        (holding ?s - swords)
    
        ;It becomes true when a trap is disarmed
        ; (trap-disarmed ?loc)
        
    )

    ;Hero can move if the
    ;    - hero is at current location
    ;    - cells are connected, 
    ;    - there is no trap in current loc, and 
    ;    - destination does not have a trap/monster/has-been-destroyed
    ;Effects move the hero, and destroy the original cell. No need to destroy the sword.
    (:action move
        :parameters (?from ?to - cells)
        :precondition (and 
                        (at-hero ?from) 
                        (connected ?from ?to)
                        (not (has-trap ?from))
                        (not (has-trap ?to))
                        (not (has-monster ?to))
                        (not (is-destroyed ?to))
        )
        :effect (and 
                    (not (at-hero ?from))
                    (at-hero ?to)
                    (is-destroyed ?from)
                    ; (not (connected ?from ?to))
                    ; (not (connected ?to ?from))
        )
    )
    
    ;When this action is executed, the hero gets into a location with a trap
    (:action move-to-trap
        :parameters (?from ?to - cells)
        :precondition (and
                        (has-trap ?to) ;must have a trap
                        (arm-free) ;must be hand free (make sure when sword is destoried, hand is freed as well)
                        
                        ;conditions to move
                        ;assume that if it contains trap, then it won't contain monster/sword
                        (at-hero ?from) 
                        (connected ?from ?to)
                        (not (has-trap ?from))
                        (not (is-destroyed ?to))
        )
        :effect (and 
                    (not (at-hero ?from))
                    (at-hero ?to)
                    (is-destroyed ?from)
                )
    )

    ;When this action is executed, the hero gets into a location with a monster
    (:action move-to-monster
        :parameters (?from ?to - cells ?s - swords)
        :precondition (and 
                        (has-monster ?to) ;must have a monster
                        (holding ?s) ;must hold a sword
                        ; (not (arm-free))
                        
                        ;conditions to move
                        ;assume that if it contains monster, then it won't contain trap/sword
                        (at-hero ?from) 
                        (connected ?from ?to)
                        (not (has-trap ?from))
                        (not (is-destroyed ?to))
        )
        :effect (and 
                    (not (at-hero ?from))
                    (at-hero ?to)
                    (is-destroyed ?from)
                )
    )
    
    ;Hero picks a sword if he's in the same location
    ;make sure when sword is picked, hand is no longer free
    (:action pick-sword
        :parameters (?loc - cells ?s - swords)
        :precondition (and 
                        (at-hero ?loc) ;must at the loc
                        (at-sword ?s ?loc) ;must have a sword
                        (arm-free) ;arm must be free, assume pick-sword is correct, so when arm is free, hold sword is false as well
                        
                        ;assume that if it contains sword, then it won't contain trap/monster
                        ;(not (is-destroyed ?loc)) ;make sure room is not destoried
                      )
        :effect (and
                    (not (arm-free))
                    (not (at-sword ?s ?loc))
                    (holding ?s)
                )
    )
    
    ;Hero destroys his sword.
    ;make sure when sword is destoried, hand is free as well
    (:action destroy-sword
        :parameters (?loc - cells ?s - swords)
        :precondition (and 
                        (at-hero ?loc) ;sword is at where hero is
                        (holding ?s) ;sword is held by hero, assume pick-sword is correct
                        
                        ;do not destroy sword when there is trap/monster
                        (not (has-trap ?loc)) 
                        (not (has-monster ?loc))
                        ;(not (is-destroyed ?loc)) ;make sure room is not destoried
                      )
        :effect (and
                    (not (holding ?s))
                    (arm-free)
                    (is-destroyed ?s)
                )
    )
    
    ;Hero disarms the trap with his free arm
    (:action disarm-trap
        :parameters (?loc - cells)
        :precondition (and 
                        (at-hero ?loc) ;hero is here
                        (has-trap ?loc) ;and here has a trap
                        (arm-free) ;while hand is free, assume destroy-sword is correct
                        
                        ;assume if there is a trap, then there is no monster/sword
                        ;(not (is-destroyed ?loc)) ;make sure room is not destoried
                      )
        :effect (and
                    (not (has-trap ?loc))
                    ;(trap-disarmed ?loc)
                )
    )
    
)