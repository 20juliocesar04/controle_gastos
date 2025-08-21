# Portfolio Premium

Este repositório foi preparado para receber o desenvolvimento de um portfólio pessoal com foco em performance, acessibilidade e interações avançadas.

## Objetivo
- Construir um site com storytelling guiado por rolagem (scroll-driven)
- Obter pontuação 100/100 no Lighthouse para Performance, Acessibilidade, SEO e Boas Práticas
- Garantir Web Vitals no verde e aderência à WCAG 2.1 AA

## Tecnologias previstas
- Next.js (App Router) com TypeScript e TailwindCSS
- GSAP + ScrollTrigger + Lenis para animações e controle de rolagem
- Integração opcional com Three.js/WebGL com fallback 2D
- Contentlayer ou CMS headless para conteúdos
- Deploy em Vercel ou Cloudflare

## Funcionalidades principais
- Página inicial com hero animado, parallax sutil e barra de progresso
- Seção de projetos com filtros e estudo de caso
- Formulário de contato com validação server-side, honeypot e rate limit
- Suporte a tema claro/escuro e `prefers-reduced-motion`
- Metadados completos, JSON-LD, sitemap e canonical para SEO

## Próximos passos
1. Configurar o ambiente Next.js com Tailwind, ESLint, Prettier e Husky
2. Implementar layout e provedores (tema, animações, analytics)
3. Criar seções base (Hero, Sobre, Projetos, Stack, Contato)
4. Adicionar orquestração de rolagem com GSAP/ScrollTrigger/Lenis
5. Desenvolver API de contato e tratamento de spam
6. Realizar auditorias de performance, acessibilidade e SEO

---

*Nota:* a geração automática de um projeto Next.js via `create-next-app` não foi possível devido a restrições de acesso ao repositório do npm.
