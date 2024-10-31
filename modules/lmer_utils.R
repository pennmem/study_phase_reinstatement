library(numDeriv)

check_conv <- function(mod) {
    if(!("code" %in% names(mod@optinfo$conv$lme4))) {
        return(TRUE)
    } else if((mod@optinfo$conv$opt == 0) & (mod@optinfo$conv$lme4$code == 0)) {
        return(TRUE)
    } else {
        return(FALSE)
    }
}

get_grads <- function(mod, is_lmer = TRUE) {
    scgrad <- tryCatch(
        with(mod@optinfo$derivs, solve(chol(Hessian), gradient)), 
        error = function(e) e)
    if(!(inherits(scgrad, "error"))) {
        mingrad <- pmin(abs(scgrad), abs(mod@optinfo$derivs$gradient))
        print("gradient error")
    } else {
        mingrad <- abs(mod@optinfo$derivs$gradient)
    }
    maxmingrad <- max(mingrad)
    max_grad <- maxmingrad
    if (is_lmer) {
        max_rel_grad <- max(abs(mod@optinfo$derivs$gradient/mod@theta))
    } else {
        pars <- getME(mod, c("theta", "fixef"))
        max_rel_grad <- max(abs(mod@optinfo$derivs$gradient/unlist(pars)))
    }
    list(max_grad = max_grad,
         max_rel_grad = max_rel_grad)
}

fit_lmer <- function(formula, data, max_n_tries = 40, use_jitter = FALSE, jitter_amount = 1.0001, jitter_diff_thresh = .0001, jitter_tol_thresh = .003, tol_n_tries = 20, use_verbose = FALSE, prev_m = c(), save_path = c(), use_REML = TRUE, memberships_list = c(), update = FALSE, start = NULL) {
    m <- prev_m
    if(is.null(m)) {
        print(paste('n_tries', 0))
        if(is.null(memberships_list)) {
            print('no memberships')
            m <- lmer(formula, data = data, REML = use_REML, start = start)
        } else {
            m <- lmer(formula, data = data, REML = use_REML, start = start, memberships = memberships_list)
        }
    }
    
    conv_opt <- check_conv(m)
    max_grad <- get_grads(m)$max_grad
    
    n_tries <- 1
    print(paste('converged?', conv_opt))
    print(n_tries)
    strict_tol <- lmerControl(optCtrl=list(xtol_abs=1e-8, ftol_abs=1e-8))
    jittering <- FALSE
    n_jitters <- 0

    while(!(check_conv(m)) & (n_tries < max_n_tries)) {
        # ss <- getME(m, c("theta","fixef"))
        pars <- getME(m, "theta")
        #     m <- update(m, start=ss) # control=glmerControl(optCtrl=list(maxfun=((1e4) * n_tries))))
        print(n_tries)
        print(paste('using jitter?', use_jitter))
        print(paste('max_n_tries:', max_n_tries))
        print(paste('tol_n_tries:', tol_n_tries))
        if((n_tries > 1) & (use_jitter == TRUE)) {
            if((abs(max_grad - prev_max_grad) < jitter_diff_thresh) & ((max_grad - 0.002) > jitter_tol_thresh)) {
                print(paste('max_grad', max_grad))
                print(paste('prev_max_grad', prev_max_grad))
                print(paste('diff from tol', (max_grad - 0.002)))
                print('jittering')
                jittering <- TRUE
                n_jitters <- n_jitters + 1
                n_tries <- n_jitters
                print('pars before jitter:')
                print(pars)
                # pars_x <- runif(length(pars), pars / jitter_amount, pars * jitter_amount)
                # correlation parameters can be neative
                abs_pars <- abs(pars)
                sign_pars <- sign(pars)
                abs_pars_x <- runif(length(abs_pars), abs_pars / jitter_amount, abs_pars * jitter_amount)
                print('abs_pars_x after jitter:')
                print(abs_pars_x)
                print('sign(pars) before jitter:')
                print(sign_pars)
                pars_x <- abs_pars_x * sign_pars
                print('pars after jitter:')
                print(pars_x)
            } else {
                pars_x <- pars
            }
        } else {
            pars_x <- pars
        }
        

        if((n_tries > tol_n_tries) | (jittering == TRUE) | (update == TRUE)) {
            print('strict tol')
            m <- update(m, start=pars_x, control=strict_tol, REML=use_REML)
        } else {
            m <- update(m, start=pars_x, REML=use_REML)
        }
        
        if(!is.null(save_path)) {
            saveRDS(m, save_path)
        }
        
        prev_max_grad <- max_grad
        max_grad <- get_grads(m)$max_grad
        print(paste('max grad:', max_grad))
        n_tries <- n_tries + 1
        print(paste('n tries:', n_tries))
        print(paste('converged?', check_conv(m)))
    }
    print('end')
    # print('converged?', check_conv(m))
    print(paste(n_tries, 'tries out of', max_n_tries))
    return(m)
}
        
fit_glmer <- function(formula, data, use_family = binomial, max_n_tries = 40, use_jitter = FALSE, jitter_amount = 1.0001, jitter_diff_thresh = .0001, jitter_tol_thresh = .003, tol_n_tries = 20, use_verbose = FALSE, prev_m = c(), save_path = c(), update = FALSE) {
    m <- prev_m
    if(is.null(m)) {
        print(paste('n_tries', 0))
        m <- glmer(formula, data = data, family = use_family)
    }
    
    conv_opt <- check_conv(m)
    max_grad <- get_grads(m, is_lmer = FALSE)$max_grad
    
    n_tries <- 1
    print(paste('converged?', conv_opt))
    print(n_tries)
    strict_tol <- glmerControl(optCtrl=list(xtol_abs=1e-8, ftol_abs=1e-8))
    jittering <- FALSE
    n_jitters <- 0

    while(!(check_conv(m)) & (n_tries < max_n_tries)) {
        pars <- getME(m, c("theta", "fixef"))
        #     m <- update(m, start=ss) # control=glmerControl(optCtrl=list(maxfun=((1e4) * n_tries))))
        print(n_tries)
        print(paste('using jitter?', use_jitter))
        print(paste('max_n_tries:', max_n_tries))
        print(paste('tol_n_tries:', tol_n_tries))
        if((n_tries > 1) & (use_jitter == TRUE)) {
            if((abs(max_grad - prev_max_grad) < jitter_diff_thresh) & ((max_grad - 0.002) > jitter_tol_thresh)) {
                print(paste('max_grad', max_grad))
                print(paste('prev_max_grad', prev_max_grad))
                print(paste('diff from tol', (max_grad - 0.002)))
                print('jittering')
                jittering <- TRUE
                n_jitters <- n_jitters + 1
                n_tries <- n_jitters
                print('pars before jitter:')
                print(pars)
                # pars_x <- runif(length(pars), pars / jitter_amount, pars * jitter_amount)
                # correlation parameters can be negative
                pars_unlist <- unlist(as.relistable(pars))
                abs_pars <- abs(pars_unlist)
                sign_pars <- sign(pars_unlist)
                abs_pars_x <- runif(length(abs_pars), abs_pars / jitter_amount, abs_pars * jitter_amount)
                print('abs_pars_x after jitter:')
                print(abs_pars_x)
                print('sign(pars) before jitter:')
                print(sign_pars)
                pars_x_unlist <- abs_pars_x * sign_pars
                pars_x <- relist(pars_x_unlist)
                print(pars_x)
            } else {
                pars_x <- pars
            }
        } else {
            pars_x <- pars
        }
        

        if((n_tries > tol_n_tries) | (jittering == TRUE) | (update == TRUE)) {
            print('strict tol')
            m <- update(m, start=pars_x, control=strict_tol)
        } else {
            m <- update(m, start=pars_x)
        }
        
        if(!is.null(save_path)) {
            saveRDS(m, save_path)
        }
        
        prev_max_grad <- max_grad
        max_grad <- get_grads(m, is_lmer = FALSE)$max_grad
        print(paste('max grad:', max_grad))
        n_tries <- n_tries + 1
        print(paste('n tries:', n_tries))
        print(paste('converged?', check_conv(m)))
    }
    print('end')
    print('converged?', check_conv(m))
    print(paste(n_tries, 'tries out of', max_n_tries))
    return(m)
}