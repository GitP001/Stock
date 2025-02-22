import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  // Set transparent status bar
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );
  runApp(const NewsApp());
}

class NewsApp extends StatelessWidget {
  const NewsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'News App',
      theme: ThemeData.dark(),
      home: const NewsHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// Simple NewsArticle model
class NewsArticle {
  final String id;
  final String imageUrl;
  final String title;
  final String summary;
  final String source;
  final String readTime;

  NewsArticle({
    required this.id,
    required this.imageUrl,
    required this.title,
    required this.summary,
    required this.source,
    required this.readTime,
  });
}

class NewsHomePage extends StatefulWidget {
  const NewsHomePage({super.key});

  @override
  State<NewsHomePage> createState() => _NewsHomePageState();
}

class _NewsHomePageState extends State<NewsHomePage> {
  int _selectedIndex = 0;
  final PageController _pageController = PageController();

  // Initially, two static articles for demonstration
  // We'll replace them with data from the backend
  List<NewsArticle> articles = [
    NewsArticle(
      id: '1',
      imageUrl: 'https://example.com/image1.jpg',
      title:
          'Two rings crafted from one billion-year-old natural diamond: Tanishq',
      summary:
          "This Valentine's Day, celebrate your eternal bond with the Soulmate Diamond Pair by Tanishq. Two rings crafted from one billion year-old-natural diamond, these rings symbolize an everlasting bond.",
      source: 'Tanishq',
      readTime: '2 min read',
    ),
    NewsArticle(
      id: '2',
      imageUrl: 'https://example.com/image2.jpg',
      title: 'Global Climate Summit Announces Breakthrough Agreement',
      summary:
          'World leaders reach historic consensus on ambitious climate action goals, setting new standards for environmental protection and sustainable development.',
      source: 'World News',
      readTime: '3 min read',
    ),
  ];

  @override
  void initState() {
    super.initState();
    // Attempt to fetch real articles from the backend
    _fetchArticlesFromBackend();
  }

  Future<void> _fetchArticlesFromBackend() async {
    // Replace with your local or deployed backend URL
    const String backendUrl = 'http://127.0.0.1:5000/api/news';

    try {
      final response = await http.get(Uri.parse(backendUrl));
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);

        // Transform JSON data into a list of NewsArticle objects
        setState(() {
          articles =
              data.map((item) {
                return NewsArticle(
                  id: item['id']?.toString() ?? '',
                  imageUrl:
                      item['image_url'] ??
                      'https://example.com/placeholder.jpg',
                  title: item['title'] ?? 'No Title',
                  summary: item['snippet'] ?? 'No Summary',
                  source: item['source'] ?? 'Unknown Source',
                  readTime: '2 min read', // Hard-coded or parse from item
                );
              }).toList();
        });
      } else {
        print('Failed to load articles. Status code: ${response.statusCode}');
      }
    } catch (e) {
      print('Error fetching articles: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Main Content
          PageView.builder(
            controller: _pageController,
            scrollDirection: Axis.vertical,
            itemCount: articles.length,
            itemBuilder: (context, index) {
              return ArticleCard(article: articles[index]);
            },
          ),

          // Navigation Bar
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              height: 83,
              decoration: BoxDecoration(
                color: Colors.black,
                border: Border(
                  top: BorderSide(color: Colors.grey[900]!, width: 0.5),
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildNavItem(0, Icons.home, 'Home'),
                  _buildNavItem(1, Icons.grid_view, 'Categories'),
                  _buildNavItem(2, Icons.person, 'Profile'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String label) {
    return InkWell(
      onTap: () => setState(() => _selectedIndex = index),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            color: _selectedIndex == index ? Colors.white : Colors.grey,
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              color: _selectedIndex == index ? Colors.white : Colors.grey,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class ArticleCard extends StatelessWidget {
  final NewsArticle article;

  const ArticleCard({super.key, required this.article});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 844,
      width: 390,
      color: Colors.black,
      child: Stack(
        children: [
          // Image Section
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: 380,
            child: Hero(
              tag: article.id,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Image.network(
                    article.imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) {
                      return Container(
                        color: Colors.grey[900],
                        child: const Icon(Icons.image, size: 50),
                      );
                    },
                  ),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.black.withOpacity(0.7),
                          Colors.transparent,
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Content Section
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            height: 464,
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Colors.black, Colors.grey[900]!],
                ),
              ),
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    article.title,
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    article.summary,
                    style: const TextStyle(
                      fontSize: 18,
                      color: Colors.white70,
                      height: 1.5,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        article.source,
                        style: TextStyle(color: Colors.grey[400], fontSize: 14),
                      ),
                      Text(
                        article.readTime,
                        style: TextStyle(color: Colors.grey[400], fontSize: 14),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Interaction Buttons
          Positioned(
            right: 16,
            bottom: 120,
            child: Column(
              children: [
                _buildInteractionButton(Icons.share),
                const SizedBox(height: 16),
                _buildInteractionButton(Icons.bookmark_border),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInteractionButton(IconData icon) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: IconButton(
        icon: Icon(icon),
        color: Colors.white,
        onPressed: () {},
      ),
    );
  }
}
